# RB-274 - Erros 5xx na catalog-api após implantação

**Tipo:** runbook
**Serviço:** catalog-api
**Alerta:** OPS-4821
**Equipe responsável:** plataforma
**Ambiente:** laboratório fictício da aula

## Objetivo e limites

Este runbook orienta a investigação de erros HTTP 5xx na catalog-api quando uma implantação recente pode ter alterado o comportamento do serviço. Ele não autoriza rollback automático. O operador precisa confirmar a relação entre a mudança e o sintoma, registrar evidências e obter a aprovação do responsável pelo incidente antes de reverter uma versão. O procedimento não cobre indisponibilidade do banco de catálogo, falha de rede entre serviços nem erro provocado por carga acima da capacidade planejada; esses cenários exigem diagnóstico próprio (RB-262 para o banco de catálogo, RB-301 para a malha de rede interna).

A catalog-api atende consultas de produto vindas da aplicação de loja. Ela depende de um banco de catálogo para leitura, de um cache Redis para respostas de produto e de um serviço de preços (pricing-service) para compor parte das respostas. Uma mesma resposta 5xx pode surgir de uma exceção introduzida no código, de configuração ausente, de uma dependência indisponível ou de esgotamento de recursos. Por isso, a hora de início dos erros é uma pista, não uma prova da causa.

Última revisão deste documento: setembro de 2026, depois do PM-021. Revisões anteriores tratavam o rollback como primeira ação; essa orientação foi retirada.

## Pré-requisitos de acesso

- Acesso de leitura ao namespace `catalogo` no cluster `lab-prd-sa1` (grupo `plataforma-leitura`).
- Acesso ao Grafana do laboratório, pasta "Catálogo", painel "catalog-api / visão por revisão".
- Acesso ao Loki pelo Grafana (fonte de dados `loki-lab`).
- Permissão de `rollout undo` só para o grupo `plataforma-plantao`. Quem não está nesse grupo executa o diagnóstico e pede a ação para o plantonista.
- Canal do incidente aberto no comunicador interno com o padrão `#inc-catalog-<data>`.

```bash
# confirma o contexto antes de começar
kubectl config current-context
kubectl -n catalogo get deploy catalog-api -o wide
```

## Sinais que ativam o procedimento

O alerta OPS-4821 dispara quando a taxa de respostas 5xx ultrapassa 2% das requisições por cinco minutos consecutivos, medida no próprio serviço (não no ingress). Compare a curva de erros com o início e o término da implantação. Verifique se a falha está concentrada nos pods da nova revisão ou se atinge igualmente as revisões antigas. Confira a prontidão dos pods, a quantidade de reinícios, a latência de consultas simples e os logs de aplicação com o identificador da revisão. Preserve pelo menos uma amostra de requisição falha, com dados sensíveis removidos.

Uma página de produto que falha por timeout no serviço de preços pode parecer a mesma regressão aos olhos do usuário. Se os erros começaram antes da implantação, se a revisão antiga apresenta a mesma falha ou se o banco não responde, interrompa a hipótese de rollback e procure a equipe responsável pela dependência. A ausência dessas verificações pode restaurar uma versão antiga sem resolver o incidente.

Expressão do alerta, para referência (a regra vive no repositório de alertas da plataforma, arquivo `catalogo/catalog-api.rules.yaml`):

```promql
# taxa de 5xx da catalog-api em 5 minutos, base do OPS-4821
sum(rate(http_server_requests_seconds_count{namespace="catalogo",service="catalog-api",status=~"5.."}[5m]))
/
sum(rate(http_server_requests_seconds_count{namespace="catalogo",service="catalog-api"}[5m]))
> 0.02
```

Existe também o alerta OPS-4822 (latência p99 acima de 1,2 s por dez minutos). Ele costuma disparar junto quando o pricing-service está lento, e quase nunca quando o problema é só de revisão. Não é regra, é observação dos últimos meses.

## Leitura inicial dos painéis

Abra o painel "catalog-api / visão por revisão" e ajuste o intervalo para começar quinze minutos antes do início da implantação. O painel tem quatro linhas: tráfego e erros por revisão, prontidão por revisão, latência por rota e dependências. A linha de dependências mostra o pool de conexões com o banco (HikariCP), a taxa de acerto do cache e a latência das chamadas ao pricing-service. Muita gente pula essa última linha porque ela fica abaixo da dobra da tela; role até o fim antes de concluir qualquer coisa.

```promql
# 5xx separados por revisão (o label pod-template-hash vem do ReplicaSet)
sum by (pod_template_hash) (
  rate(http_server_requests_seconds_count{namespace="catalogo",service="catalog-api",status=~"5.."}[2m])
)

# 5xx por rota, para separar leitura simples de rotas que compõem preço
sum by (uri) (
  rate(http_server_requests_seconds_count{namespace="catalogo",service="catalog-api",status=~"5.."}[2m])
)

# latência p99 das chamadas ao pricing-service, vista pela catalog-api
histogram_quantile(0.99,
  sum by (le) (rate(http_client_requests_seconds_bucket{namespace="catalogo",client_name="pricing-service"}[5m]))
)
```

## Sequência de diagnóstico

1. Anote o identificador da versão implantada, o horário da mudança, a taxa de 5xx anterior e a taxa atual. Registre também o número de pods saudáveis por revisão.
2. Compare requisições de leitura simples (`GET /v1/products/{sku}`) com requisições que consultam preços (`GET /v1/products/{sku}/offers` e `GET /v1/listings`). Se somente o segundo grupo falhar, investigue a dependência antes de atribuir a causa ao código da catalog-api.
3. Confira eventos de prontidão e reinício. Pods que nunca ficam prontos após a mudança apontam para inicialização ou configuração; pods prontos com exceções em uma rota apontam para falha de execução. Pods que ficam prontos, recebem tráfego e depois perdem a prontidão merecem atenção especial: a contagem total de pods parece normal enquanto a capacidade útil cai.
4. Consulte o histórico de mudanças do mesmo intervalo. Uma rotação de credencial, alteração de Secret, mudança de ConfigMap ou de rota no ingress pode coincidir com a implantação e produzir a mesma correlação temporal.
5. Extraia dos logs as primeiras mensagens WARN e ERROR de cada pod da revisão nova, a partir do horário de criação do pod. A primeira mensagem anormal costuma aparecer segundos antes do primeiro 5xx e se perde facilmente no meio das linhas de health check.
6. Peça à equipe de aplicação que compare a configuração exigida pela nova versão com a configuração presente no ambiente. Não copie valores secretos para o registro do incidente.
7. Faça uma requisição de teste contra um pod de cada revisão usando port-forward, com a mesma rota e o mesmo SKU de teste.
8. Verifique se o pricing-service, o banco e o cache apresentam degradação no mesmo intervalo, consultando os painéis da equipe dona de cada um.
9. Formule a hipótese mais forte e anote qual evidência a sustenta e qual observação a refutaria. Esta anotação acompanha o pedido de aprovação.
10. Envie no canal do incidente o pedido de aprovação ao responsável pelo incidente, com hipótese, evidências, revisão de destino e janela de observação proposta. Sem resposta explícita, nenhuma ação de reversão é executada.
11. Após a aprovação, registre no ticket do incidente o horário, quem aprovou e a revisão de destino, e só então siga para a seção "Decisão de estabilização".

Comandos de apoio para os passos 1, 3, 5 e 7:

```bash
# revisões do Deployment e imagem de cada uma
kubectl -n catalogo rollout history deploy/catalog-api
kubectl -n catalogo get rs -l app=catalog-api \
  -o custom-columns=RS:.metadata.name,IMG:.spec.template.spec.containers[0].image,PRONTOS:.status.readyReplicas

# pods, reinícios e idade, com o hash da revisão
kubectl -n catalogo get pods -l app=catalog-api -L pod-template-hash

# eventos de prontidão (Readiness probe failed) dos últimos minutos
kubectl -n catalogo get events --field-selector involvedObject.kind=Pod \
  --sort-by=.lastTimestamp | grep -i -E "readiness|back-off|killing"

# logs do container anterior, quando o pod reiniciou
kubectl -n catalogo logs <pod> --previous --tail=200

# port-forward para um pod específico e requisição de teste
kubectl -n catalogo port-forward pod/<pod> 18080:8080
curl -s -o /dev/null -w "%{http_code} %{time_total}\n" \
  http://localhost:18080/v1/products/SKU-TESTE-0001/offers
```

Consultas de log no Loki (LogQL):

```logql
# erros e avisos de um pod da revisão nova, em ordem
{namespace="catalogo", app="catalog-api", pod=~"catalog-api-<hash>-.*"} | json | level=~"WARN|ERROR"
```

### Armadilhas conhecidas na leitura dos logs

Os logs da catalog-api são JSON de uma linha, mas a exceção vem num campo `exception` com várias linhas. O Grafana corta o campo em 1.000 caracteres na visualização de tabela; abra a linha completa para ver a causa encadeada (`Caused by`). Mensagens de `HikariPool` com "Connection is not available" nem sempre indicam problema no banco: elas também aparecem quando threads ficam presas esperando outra dependência e seguram conexões por mais tempo. A mensagem "Cache miss em massa" aparece depois de qualquer reinício de pod, porque o cache local de segundo nível (Caffeine) começa vazio; ela não indica falha do Redis.

## Decisão de estabilização

Considere a reversão quando os erros surgirem com a revisão nova, a revisão anterior tiver atendido as mesmas consultas normalmente e não houver sinal mais forte de falha em dependência. O responsável pelo incidente deve aprovar a ação e combinar uma janela de observação. Reverter é uma intervenção de produção, mesmo quando o comando é curto. Registre quem autorizou, qual versão era a anterior e como a equipe confirmará que a mudança produziu o efeito esperado. A decisão de estabilizar não é uma decisão sobre a causa; ela apenas tira do tráfego a revisão que está associada ao sintoma, e a equipe deve continuar tratando a hipótese como hipótese até que a investigação posterior a confirme ou a derrube. Isso vale inclusive para o caso em que o rollback resolve o sintoma: uma revisão antiga pode funcionar porque não exercita a mesma rota, porque usa um padrão diferente de conexão com o pricing-service, ou porque a simples recriação dos pods limpou um estado ruim de cache, e nenhuma dessas explicações aponta para o mesmo trabalho de correção. Durante o PM-021, a equipe só teve segurança para pedir a aprovação depois de juntar três peças diferentes: a falha concentrada nos pods da revisão nova, a requisição de teste bem sucedida contra a revisão antiga e a mensagem de configuração ausente nos logs sanitizados. Qualquer uma dessas peças sozinha teria sustentado outras leituras. Quando o responsável pelo incidente aprovar, combine também quem fica olhando o quê durante a janela de observação: uma pessoa nos painéis de 5xx e prontidão, outra na requisição representativa, e o próprio responsável no canal, respondendo à liderança e às equipes vizinhas. Se a revisão anterior também teve problemas conhecidos (por exemplo, um ticket aberto de vazamento de memória), anote isso no pedido de aprovação, porque a janela de observação precisa olhar também esse sintoma. Por fim, verifique se existe uma implantação em andamento de outro serviço que dependa da catalog-api, como o storefront-bff; reverter a catalog-api no meio de uma implantação do consumidor já gerou uma combinação de versões que ninguém tinha testado.

Depois da aprovação, restaure a última revisão estável pelo processo operacional da equipe. Não improvise uma versão intermediária e não altere simultaneamente o banco ou o serviço de preços: mudanças paralelas dificultam a atribuição de causa. Acompanhe a taxa de 5xx, a prontidão, os reinícios e uma consulta de produto representativa por dez minutos. Se a taxa não cair, interrompa novas reversões e volte ao diagnóstico das dependências.

```bash
# somente com aprovação registrada no ticket do incidente
kubectl -n catalogo rollout undo deploy/catalog-api --to-revision=<revisao-estavel>
kubectl -n catalogo rollout status deploy/catalog-api --timeout=5m
```

O pipeline de implantação (ArgoCD, aplicação `catalog-api-prd`) vai marcar a aplicação como fora de sincronia depois do `rollout undo`. Isso é esperado. Suspenda a sincronização automática da aplicação antes da reversão, para que o ArgoCD não reaplique a revisão nova em seguida, e abra o pedido de reversão no repositório de manifestos assim que o incidente estiver estável.

## Verificação e encerramento

O critério de sucesso exige três observações juntas: a taxa de 5xx retorna ao patamar anterior, os pods permanecem prontos e uma consulta representativa de catálogo funciona de ponta a ponta. Uma melhora de poucos segundos não encerra o incidente. Anote o horário da recuperação, a revisão ativa, a curva de erros após a ação e as pendências para correção definitiva. A correção do código ou da configuração defeituosa pertence ao trabalho posterior, não ao ato de estabilizar.

Consulta representativa usada pela equipe: `GET /v1/products/SKU-TESTE-0001/offers?region=SUL`, com o cabeçalho `X-Lab-Synthetic: true` para não contaminar as métricas de negócio. O SKU de teste existe em todos os ambientes do laboratório e tem preço em todas as regiões.

```promql
# patamar de referência: 5xx dos sete dias anteriores no mesmo horário
sum(rate(http_server_requests_seconds_count{namespace="catalogo",service="catalog-api",status=~"5.."}[5m] offset 7d))
/
sum(rate(http_server_requests_seconds_count{namespace="catalogo",service="catalog-api"}[5m] offset 7d))
```

## Escalonamento e evidências

Escalone para a equipe de aplicação (catálogo) se a revisão antiga também falhar, se a reversão não reduzir os erros ou se uma dependência apresentar degradação. Escalone para a equipe de preços se a latência das chamadas ao pricing-service estiver acima do timeout configurado na catalog-api. Inclua versão, horários, séries de erro e prontidão, amostras sanitizadas de logs e a hipótese descartada. Nunca inclua tokens, cabeçalhos de autenticação ou dados pessoais de clientes. O post-mortem PM-021 descreve um incidente anterior dessa família, mas o relato histórico não substitui estas verificações em um incidente novo.

| Situação | Para quem | Como |
|---|---|---|
| Revisão antiga também falha | catálogo (aplicação) | canal do incidente, menção ao grupo `@catalogo-plantao` |
| pricing-service lento ou com erro | preços | página pelo alerta da própria equipe de preços |
| banco de catálogo sem resposta | dados | seguir RB-262 |
| mais de 30 minutos sem estabilizar | gerência de plantão | ligação pela escala |

## Histórico deste runbook

- 2026-09: inclusão da comparação explícita entre revisões, da requisição de teste por port-forward e do pedido de aprovação com observação refutadora (ações do PM-021).
- 2026-06: troca da consulta de logs do Kibana para o Loki.
- 2026-03: criação, a partir de anotações do plantão.
