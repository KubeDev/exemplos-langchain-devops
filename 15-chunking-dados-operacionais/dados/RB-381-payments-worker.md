# RB-381 - Fila parada no payments-worker após rotação de credencial

**Tipo:** runbook
**Serviço:** payments-worker
**Alerta:** PAY-7712
**Equipe responsável:** pagamentos
**Ambiente:** laboratório fictício da aula

## Objetivo e limites

Este procedimento trata da perda de consumo da fila de pagamentos após a rotação da credencial usada pelo worker para se autenticar no broker. Seu objetivo é restabelecer o consumo sem expor segredos e sem processar mensagens duas vezes por uma intervenção precipitada. A simples presença de uma fila acumulada não prova falha de autenticação: lentidão no processamento, indisponibilidade do broker e aumento legítimo da taxa de entrada produzem sintomas parecidos.

O payments-worker recebe mensagens de cobrança, confirma seu processamento e publica um resultado para a aplicação de pedidos. A fila funciona como amortecedor entre a entrada de solicitações e o processamento. Quando os workers param, o atraso cresce mesmo que a aplicação de pedidos continue aceitando novas solicitações. O tempo de espera do cliente pode aumentar antes de surgir um erro direto na API. A equipe deve considerar esse impacto ao comunicar o incidente.

Este runbook não cobre: falha do gateway de cartão (ver RB-377), erro de schema na mensagem de cobrança (ver RB-390), nem manutenção programada do cluster do broker, que é conduzida pela equipe de mensageria com janela própria.

## Condições para usar este runbook

Use o runbook quando o alerta PAY-7712 indicar crescimento sustentado do atraso e os logs dos workers mostrarem falha de autenticação próxima ao horário de rotação da credencial. Registre o início da rotação, a versão de Secret esperada, a versão referenciada pelo deployment e a hora em que cada worker iniciou. Não registre o valor da credencial em tickets, terminal compartilhado ou captura de tela da aula.

Se os workers estão autenticados e processando lentamente, siga a investigação de desempenho. Se o broker inteiro está indisponível, escale para a equipe que o opera. Se uma mensagem específica provoca repetidos erros de negócio, isole essa mensagem pelo procedimento de fila de quarentena; reiniciar workers sem entender o erro apenas repete a falha.

### Referências rápidas

- Namespace: `pagamentos`
- Deployment: `payments-worker`
- Fila de entrada: `pagamentos.cobranca.v2`
- Fila de quarentena: `pagamentos.cobranca.quarentena`
- Exchange de resultado: `pedidos.resultado`
- Usuário do broker: `svc-payments-worker`
- Secret montado no pod: `payments-broker-cred` (o nome versionado fica na anotação `pagamentos.lab/secret-versao`)
- Painel: "Pagamentos / Fila e consumo" (aba "Entrada x Confirmação")
- Canal de incidente: `#inc-pagamentos`

## Diagnóstico em ordem

1. Compare a curva de mensagens pendentes, a taxa de entrada e a taxa de confirmação. Uma fila que cresce porque a entrada duplicou exige resposta diferente de uma fila com consumo zero.
2. Observe erros de autenticação nos logs sem imprimir cabeçalhos, senhas ou tokens. Conte quantos workers apresentam o erro e confira se ele começou após a rotação.
3. Consulte o identificador e a versão do Secret aprovado no gerenciador de segredos. Compare apenas identificadores e datas com a referência que o deployment usa.
4. Verifique quando os processos foram iniciados. Alguns workers leem credenciais somente na inicialização; nesses casos, corrigir um Secret não atualiza o valor já carregado na memória do processo.
5. Confirme com o responsável pelo broker se a credencial antiga foi revogada e se a nova já está ativa. Uma diferença de horário entre publicação e revogação pode explicar falhas intermitentes.
6. Registre a hipótese, a evidência a favor e um sinal que a refutaria. Peça aprovação antes de reiniciar componentes que processam pagamentos.

### Consultas de apoio

```promql
# Entrada x confirmação na fila de cobrança (mensagens por segundo, janela de 5 min)
sum(rate(broker_queue_messages_published_total{queue="pagamentos.cobranca.v2"}[5m]))
sum(rate(broker_queue_messages_acked_total{queue="pagamentos.cobranca.v2"}[5m]))

# Mensagens prontas aguardando consumo
max(broker_queue_messages_ready{queue="pagamentos.cobranca.v2"})

# Consumidores ativos vistos pelo broker (cai antes do atraso aparecer no painel)
max(broker_queue_consumers{queue="pagamentos.cobranca.v2"})
```

```bash
# Erros de autenticação por pod nos últimos 30 min (não imprime a mensagem inteira)
kubectl -n pagamentos logs -l app=payments-worker --since=30m --prefix \
  | grep -c 'ACCESS_REFUSED'

# Horário de início de cada pod e versão do Secret anotada no template
kubectl -n pagamentos get pods -l app=payments-worker \
  -o custom-columns=POD:.metadata.name,INICIO:.status.startTime,RESTARTS:.status.containerStatuses[0].restartCount
kubectl -n pagamentos get deploy payments-worker \
  -o jsonpath='{.spec.template.metadata.annotations.pagamentos\.lab/secret-versao}{"\n"}'
```

```logql
# Mesma busca no agregador de logs, agrupada por pod
sum by (pod) (count_over_time({namespace="pagamentos", app="payments-worker"} |= "ACCESS_REFUSED" [5m]))
```

## Interpretação dos sinais

O atraso da fila é um sinal tardio. Quando o PAY-7712 dispara, o broker normalmente já enxerga menos consumidores do que o esperado há alguns minutos, porque o alerta só avalia o atraso depois de uma janela de sustentação para não reagir a picos curtos do fechamento de lote da aplicação de pedidos. Por isso a primeira pergunta não é quanto a fila cresceu, e sim desde quando a confirmação parou de acompanhar a entrada. Se a entrada está estável e a confirmação caiu, o problema está no lado do consumo. Se a entrada subiu e a confirmação também subiu, mas menos, o problema é de capacidade e este runbook provavelmente não se aplica. Uma confirmação que cai em degraus, um pod de cada vez, é típica de consumidores que perdem a conexão em momentos diferentes; uma queda simultânea de todos os pods aponta mais para o broker ou para a rede do que para a credencial. Os workers mantêm conexões de longa duração e as renovam periodicamente; um worker com a credencial antiga em memória pode continuar funcionando por vários minutos depois da revogação, até o momento em que precisa abrir uma conexão nova. Isso faz a falha parecer intermitente e espalhada no tempo, o que costuma levar a equipe a suspeitar de instabilidade de rede antes de olhar a credencial. Outro ponto que confunde: o probe de readiness do worker verifica apenas o servidor HTTP interno e o acesso ao armazenamento de idempotência, não a conexão com o broker. Um pod sem conexão continua aparecendo como pronto no `kubectl get pods`, sem reinícios, e o Deployment parece saudável. Não use o estado dos pods como evidência de que o consumo está ocorrendo. Os logs também têm armadilhas. A mensagem de falha de reconexão é emitida em nível WARN nas primeiras tentativas e só passa a ERROR quando o consumidor desiste do canal, e o cliente do broker repete tentativas com backoff exponencial até o limite configurado; em um período curto o volume de linhas é pequeno e fica perdido no meio das mensagens de cobrança processada e de health check. Filtrar por nível ERROR sozinho atrasa a percepção. Procure também a mensagem de confirmação (ack) que falhou por canal fechado: ela indica que havia mensagens em voo no momento da queda, que voltam para a fila e serão reentregues, e é justamente essa reentrega que exige atenção à idempotência mais adiante. Por fim, a fila de quarentena deve ficar estável durante um incidente de credencial. Se ela cresce junto com a fila principal, há outro problema em curso (geralmente mensagem malformada ou erro de negócio repetido) e reiniciar workers não resolve. Registre no ticket do incidente os horários exatos do primeiro WARN de reconexão e do primeiro ack falho de cada pod; eles são usados depois para reconstruir a linha do tempo e comparar com o horário da revogação informado pela equipe de mensageria.

## Procedimento de estabilização

Se a referência ao Secret estiver errada, corrija-a pelo processo aprovado de mudança antes de qualquer reinício. Se a referência estiver correta, mas os workers ainda carregarem a versão antiga, siga os passos abaixo. Reinicie em lotes pequenos e acompanhe as confirmações de mensagens; desligar todos os workers ao mesmo tempo amplia o atraso e elimina capacidade de recuperação. Não altere o formato de mensagem nem limpe a fila durante a rotação.

1. Abra (ou atualize) o ticket do incidente com o horário da rotação, a versão de Secret aprovada e a versão anotada no Deployment.
2. Congele mudanças no namespace `pagamentos` anunciando no canal de incidente; pause qualquer pipeline de deploy do payments-worker em andamento.
3. Confirme que o HPA não está no máximo de réplicas. Se estiver, anote o valor atual: o reinício de um lote reduz temporariamente a capacidade e o HPA pode reagir.
4. Liste os pods com horário de início e separe os que iniciaram antes da rotação; esses são os candidatos ao reinício.
5. Verifique a fila de quarentena e a taxa de mensagens reentregues (`redelivered`). Se a quarentena estiver crescendo, pare aqui e siga RB-390.
6. Teste a credencial vigente sem afetar o tráfego: suba um pod de diagnóstico com o mesmo Secret e confirme que a conexão é aceita (ver bloco abaixo). Apague o pod de diagnóstico em seguida.
7. Solicite aprovação explícita no ticket do líder técnico de pagamentos e do gerente de incidente para o reinício. Sem as duas aprovações registradas, não prossiga. Em horário de fechamento financeiro (dias 1 e 15, das 00:00 às 03:00 UTC), também é necessário o aval da operação financeira.
8. Reinicie o primeiro lote, no máximo um pod ou 25% das réplicas (o que for menor), apagando os pods selecionados um a um.
9. Aguarde o novo pod registrar a conexão ao broker e as primeiras confirmações; observe por pelo menos 3 minutos a taxa de confirmação e o contador de reentregas.
10. Repita os passos 8 e 9 para os lotes seguintes até não restar pod iniciado antes da rotação.
11. Retire o congelamento de mudanças e registre no ticket a versão do Secret em uso e o horário de normalização.

```bash
# Passo 6: pod de diagnóstico com o mesmo Secret (só testa a conexão, não consome)
kubectl -n pagamentos run pw-diag --rm -it --restart=Never \
  --image=registro.lab.interno/pagamentos/payments-worker:2.18.3 \
  --overrides='{"spec":{"serviceAccountName":"payments-worker"}}' \
  -- /app/bin/broker-check --credencial-arquivo /var/run/secrets/broker/credencial
# saída esperada: "conexão aceita pelo broker (vhost=pagamentos)"

# Passo 8: apagar um pod antigo por vez (o ReplicaSet cria o substituto)
kubectl -n pagamentos delete pod <pod-antigo> --wait=false

# Passo 9: acompanhar o novo pod
kubectl -n pagamentos logs -f <pod-novo> | grep -E 'conectado ao broker|consumindo'
```

Depois de cada lote, verifique se as novas instâncias se autenticam, consomem mensagens e confirmam o processamento. Observe também a fila de quarentena e os identificadores de transação para detectar repetição indevida. A queda do atraso deve ser sustentada, não um efeito temporário de uma única instância. Se a autenticação continuar falhando, pare novas tentativas, preserve os logs sanitizados e peça verificação da credencial e da política de acesso pelo responsável pelo broker.

### Por que não usar `kubectl rollout restart`

O `rollout restart` respeita o `maxUnavailable` do Deployment, mas cria pods novos em paralelo com o surge configurado e não dá tempo de observar cada lote. Em incidentes anteriores ele provocou uma rajada de reentregas porque vários pods antigos foram encerrados com mensagens em voo ao mesmo tempo. Use-o apenas fora de incidente, em rotação programada com a fila vazia ou quase vazia.

## Verificação de duplicidade

Mensagens que estavam em voo quando o canal caiu são reentregues. O worker consulta o armazenamento de idempotência pela chave `txn_id` antes de chamar o gateway, então uma reentrega normalmente resulta em "cobrança já processada, ignorando". Ainda assim, confira:

```bash
# Contagem de reentregas descartadas por idempotência após o reinício
kubectl -n pagamentos logs -l app=payments-worker --since=20m | grep -c 'já processada'
```

Se aparecerem duas confirmações de cobrança para o mesmo `txn_id` com `gateway_ref` diferentes, trate como incidente separado de duplicidade e acione a operação financeira.

## Critérios de recuperação

Considere o serviço estabilizado quando erros de autenticação cessarem, a taxa de confirmação superar a taxa de entrada por tempo suficiente para reduzir o atraso e não houver crescimento anormal da fila de quarentena. Confirme com a aplicação de pedidos que novas solicitações recebem resultado dentro do intervalo esperado. Registre a versão do Secret em uso e o horário de normalização; não registre o segredo.

## Comunicação

Durante o incidente, publique no canal de status a cada 15 minutos: horário de início, impacto percebido (atraso no resultado de pagamento, não perda de pedidos), ação em curso e próxima atualização. Evite estimar prazo de normalização antes de o primeiro lote mostrar consumo. Não cite nomes de usuários do broker nem versões de Secret em canais abertos.

## Escalonamento e aprendizado

Escalone quando a credencial aprovada não for aceita, quando o broker reportar falha geral ou quando o processamento voltar com risco de duplicação. Leve gráficos de entrada, confirmação e atraso, versões de Secret, horários de inicialização e amostras sanitizadas dos erros. O post-mortem PM-034 descreve um caso em que o Secret correto já estava disponível, mas os processos antigos continuaram com a credencial anterior. Ele ajuda a formular hipóteses; este runbook determina as verificações necessárias agora.

| Situação | Para quem escalar | Como |
|---|---|---|
| Credencial nova rejeitada pelo broker | Mensageria (plantão) | página no rotativo "mensageria-primário" |
| Broker indisponível para todos os consumidores | Mensageria + gerente de incidente | página + ponte de incidente |
| Suspeita de cobrança duplicada | Operação financeira | ticket prioritário + ligação |
| Quarentena crescendo | Pagamentos (desenvolvimento) | RB-390 |

## Histórico deste runbook

- v1: versão inicial, foco em fila acumulada.
- v2: incluída a comparação entre Secret declarado e credencial carregada no processo (após PM-034).
- v3: passo de pod de diagnóstico e janela de fechamento financeiro na aprovação.
