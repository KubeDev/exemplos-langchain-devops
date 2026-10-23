# RB-905 - Volume temporário cheio no image-processor

**Tipo:** runbook
**Serviço:** image-processor
**Alerta:** MED-3304
**Equipe responsável:** mídia
**Ambiente:** laboratório fictício da aula

## Objetivo e limites

Este runbook orienta a estabilização do image-processor quando o volume temporário fica cheio e os trabalhos de processamento de imagens deixam de terminar. A intervenção protege arquivos de trabalhos em andamento e evidências do incidente. Não autoriza apagar diretórios inteiros, limpar arquivos de origem ou remover dados cujo dono não tenha sido identificado. Uma fila grande, sozinha, não é razão para limpar disco: o atraso pode resultar de CPU insuficiente, de uma dependência externa lenta ou de uma entrada incomum de imagens.

O serviço recebe imagens originais, cria versões derivadas e grava arquivos intermediários antes de publicar o resultado. O armazenamento temporário deveria ser liberado ao fim de cada trabalho. Se a limpeza falha, arquivos de tarefas já concluídas se acumulam até impedir novos trabalhos. A pressão no volume pode causar reinícios dos pods; esses reinícios escondem a causa se a equipe observar apenas o estado atual do processo.

Este documento cobre o volume `scratch` montado em `/scratch` nos pods do Deployment `image-processor` (namespace `midia`). Não cobre o disco do nó, o armazenamento de objetos (`midia-originais` e `midia-derivados`) nem o banco `midia_jobs`.

## Contexto rápido para quem está de plantão

O volume `scratch` é um volume efêmero genérico: cada pod recebe um PVC próprio de 10Gi, criado junto com o pod e apagado quando o pod é removido. Um reinício de contêiner (o `RESTARTS` subindo no `kubectl get pods`) **não** apaga o volume; só a remoção do pod faz isso. Por isso o reinício não alivia o disco e o pod volta a falhar alguns minutos depois. Apagar o pod libera o espaço, mas descarta junto os intermediários de trabalhos ativos e as evidências da falha de limpeza, e o trabalho volta para a fila sem garantia de idempotência se a chave no Redis já tiver expirado. Não apague pods como primeira ação.

Dentro de `/scratch`, cada trabalho usa um diretório `/scratch/jobs/<job_id>/` com subpastas `entrada/`, `variantes/` e `verificacao/`. Existe ainda `/scratch/.probe`, usado pela sonda de vivacidade, e `/scratch/quarentena/`, onde a aplicação move arquivos de trabalhos que falharam para análise posterior. O conteúdo de `quarentena/` é retido por 72 horas pela própria aplicação; se estiver grande, isso é um sintoma a registrar, não uma solução.

## Sinais iniciais

O alerta MED-3304 indica uso elevado do volume temporário. Confirme a porcentagem ocupada, a velocidade de crescimento e o espaço livre real em cada pod. Compare o horário do alerta com aumento na taxa de entrada, implantação recente e mudanças na política de retenção. Verifique a fila de trabalhos, os reinícios e as mensagens de erro de escrita. Uma falha em armazenamento definitivo pode produzir erro de publicação mesmo com espaço temporário disponível; se esse for o caso, siga o procedimento da dependência.

Os arquivos temporários podem conter cópias de imagens ainda não publicadas. Trate nomes e caminhos como dados operacionais, mas não exponha imagens de clientes durante a investigação. Para a aula, todos os nomes e métricas são fictícios. Em um incidente real, a política de dados e os controles de acesso da equipe prevalecem sobre qualquer exemplo didático.

### Consultas de partida

```promql
# Ocupação do volume scratch por pod (o alerta MED-3304 dispara acima de 0.85 por 5 minutos)
imgproc_scratch_bytes_used{namespace="midia"} / imgproc_scratch_bytes_capacity{namespace="midia"}

# Velocidade de crescimento em bytes por segundo, janela de 10 minutos
deriv(imgproc_scratch_bytes_used{namespace="midia"}[10m])

# Idade do arquivo temporário mais antigo (métrica criada depois do PM-041)
max by (pod) (imgproc_scratch_oldest_file_age_seconds{namespace="midia"})

# Mensagens prontas na fila principal
rabbitmq_queue_messages_ready{queue="image-processor.trabalhos"}
```

```bash
# Estado dos pods e reinícios
kubectl -n midia get pods -l app=image-processor -o wide

# Último motivo de término do contêiner (OOMKilled, Error, etc.)
kubectl -n midia get pods -l app=image-processor \
  -o custom-columns=POD:.metadata.name,RESTARTS:.status.containerStatuses[0].restartCount,MOTIVO:.status.containerStatuses[0].lastState.terminated.reason
```

```logql
# Erros de escrita no volume nos últimos 30 minutos
{namespace="midia", app="image-processor"} |= "Errno 28" | json | line_format "{{.pod}} {{.message}}"
```

## Investigação ordenada

1. Anote a ocupação de cada volume, a taxa de crescimento, os reinícios e a idade do trabalho mais antigo na fila.
2. Identifique quais diretórios são temporários e quais contêm arquivos de origem ou de saída. Consulte a documentação do serviço antes de selecionar qualquer caminho para limpeza.
3. Cruze identificadores de arquivos temporários com o estado dos trabalhos. Um arquivo associado a trabalho ativo ou de estado desconhecido não pode ser removido nesta etapa.
4. Compare a taxa de entrada e a duração média de processamento com o padrão anterior. Um pico legítimo pode exigir redução temporária da entrada ou aumento de capacidade, sem indicar vazamento.
5. Verifique se houve implantação ou alteração na rotina de limpeza antes do crescimento do disco. Observe logs de falha de remoção após conclusão de trabalhos.
6. Registre a hipótese, a lista de arquivos elegíveis e a aprovação do responsável. A lista precisa permitir auditoria posterior sem copiar dados sensíveis.

### Como medir o volume por dentro do pod

Use `du` com profundidade limitada; um `du` recursivo completo pode levar minutos e concorrer por IO com os trabalhos em andamento.

```bash
# Espaço livre real no volume (não confie só na métrica se o exporter estiver reiniciando)
kubectl -n midia exec image-processor-<hash>-<id> -c processor -- df -h /scratch

# Tamanho por diretório de trabalho, só o primeiro nível, ordenado
kubectl -n midia exec image-processor-<hash>-<id> -c processor -- \
  sh -c 'du -sm /scratch/jobs/* 2>/dev/null | sort -rn | head -40'
```

### Cruzamento entre diretório e estado do trabalho

A aplicação tem um comando administrativo que lê os nomes de diretório em `/scratch/jobs`, consulta a tabela `trabalhos` em lote e imprime o estado de cada um. Ele não remove nada. A saída é um CSV com `job_id`, `estado`, `atualizado_em`, `bytes` e `pod`. Guarde o CSV no ticket do incidente; ele é a base da lista de arquivos elegíveis.

```bash
# Gera o cruzamento diretório x estado (somente leitura)
kubectl -n midia exec image-processor-<hash>-<id> -c processor -- \
  imgproc-admin scratch-report --formato csv > scratch-report-<pod>.csv

# Resumo por estado
awk -F, 'NR>1 {n[$2]++; b[$2]+=$4} END {for (e in n) printf "%-14s %6d dirs %8.1f MiB\n", e, n[e], b[e]/1048576}' scratch-report-<pod>.csv
```

Estados possíveis na tabela: `recebido`, `baixando`, `transformando`, `verificando`, `concluido`, `falhou` e `desconhecido` (este último é atribuído pelo relatório quando o `job_id` do diretório não existe no banco). Somente `concluido` com `atualizado_em` mais antigo que 15 minutos é elegível. `falhou` não é elegível sem conversa com a equipe de mídia, porque a reprocessadora pode estar lendo os intermediários para diagnóstico.

## Procedimento de estabilização

Se o espaço estiver prestes a esgotar e o sistema de filas permitir, pause novas entradas para reduzir a pressão. Com aprovação, remova somente arquivos temporários identificados como pertencentes a trabalhos concluídos. Faça a remoção em lotes pequenos, conferindo o espaço liberado e o efeito sobre o serviço após cada lote. Preserve uma amostra de evidências que ajude a reproduzir a falha de limpeza. Não remova arquivos de trabalhos ativos, mesmo quando parecem antigos.

Siga a ordem abaixo. Cada passo tem uma saída que precisa ser registrada no ticket antes do passo seguinte.

1. Abra (ou localize) o ticket do incidente e anote o horário do alerta MED-3304, a versão implantada (`kubectl -n midia get deploy image-processor -o jsonpath='{.spec.template.spec.containers[0].image}'`) e quem está conduzindo.
2. Reduza a entrada: ajuste o `prefetch` do consumidor para 1 com `imgproc-admin consumo --prefetch 1` em cada pod. Isso não para o serviço; apenas impede que cada pod puxe vários trabalhos de uma vez enquanto o disco está no limite.
3. Se a ocupação estiver acima de 95% em algum pod, pause o consumo naquele pod (`imgproc-admin consumo --pausar`). Os trabalhos que já estão em andamento continuam até terminar ou falhar; nada é cancelado.
4. Confirme que o HPA não vai criar pods novos para compensar a fila parada: `kubectl -n midia get hpa image-processor`. Se a fila estiver alta, o HPA tende a subir réplicas, o que é aceitável, mas anote o número de réplicas antes e depois.
5. Gere o relatório `scratch-report` de cada pod afetado, conforme a seção de cruzamento, e anexe os CSVs ao ticket.
6. Monte a lista de elegíveis: apenas diretórios em estado `concluido` atualizados há mais de 15 minutos. Separe uma amostra de 5 diretórios elegíveis para evidência e copie-os para `/scratch/quarentena/pm-amostra/` (cópia de metadados com `imgproc-admin scratch-amostra`, que não copia pixels).
7. Peça a aprovação do responsável técnico de mídia de plantão, colando no ticket a quantidade de diretórios, o total em MiB e o critério usado. Sem aprovação registrada no ticket, não avance. Em horário comercial, a aprovação pode vir do líder técnico de mídia; fora dele, do coordenador de incidentes.
8. Remova o primeiro lote com no máximo 200 diretórios por pod usando `imgproc-admin scratch-limpar --lista elegiveis-<pod>.txt --lote 200`. O comando recusa qualquer `job_id` cujo estado mudou desde a geração da lista.
9. Depois de cada lote, confira `df -h /scratch`, o número de reinícios e a fila. Se o espaço liberado for muito menor que o esperado pelo CSV, pare: há arquivos abertos por processos ou a lista está errada.
10. Retome o consumo gradualmente: primeiro `--retomar` com `prefetch` 1, depois de 10 minutos estáveis volte ao `prefetch` padrão. Registre os horários.
11. Mantenha o ticket aberto em observação por pelo menos 1 hora, com o painel de ocupação, reinícios e fila no mesmo intervalo.

Se o espaço voltar a cair rapidamente, interrompa a retomada e investigue a rotina de retenção; repetir a limpeza indefinidamente esconde a falha e aumenta o risco de apagar dados necessários.

## Armadilhas conhecidas

Esta seção junta o que já confundiu plantões anteriores e o que apareceu em simulações da equipe. Não é uma lista de causas: é uma lista de coisas que parecem resolver e não resolvem, ou que resolvem e cobram um preço depois. O primeiro equívoco comum é olhar o `RESTARTS` subir e concluir que o problema é memória. O image-processor usa bastante memória ao decodificar imagens grandes, e um OOMKilled ocasional em entrada com imagens de 60 megapixels ou mais é esperado e coberto por outro alerta. Quando o volume enche, porém, o motivo do término costuma ser `Error` com código de saída 1, porque a sonda de vivacidade tenta gravar `/scratch/.probe` e falha, e o kubelet reinicia o contêiner. Confira `lastState.terminated.reason` antes de propor aumento de memória. O segundo equívoco é aumentar o tamanho do volume no meio do incidente. O volume efêmero genérico é definido no template do pod, e mudar o tamanho exige um novo rollout: os pods novos nascem com volume maior e vazio, os pods antigos são encerrados levando consigo os intermediários e as evidências. Parece funcionar, a fila volta a andar, e algumas horas depois o alerta dispara de novo porque nada mudou no comportamento de limpeza. Se a decisão for aumentar o volume, faça isso depois de coletar a amostra de evidências e com o ticket de mudança aberto. O terceiro equívoco envolve o CronJob `image-processor-tmp-sweeper`. Ele existe desde antes do volume efêmero, roda de madrugada e remove diretórios com mais de 24 horas. Alguém sempre sugere rodá-lo manualmente com `kubectl create job --from=cronjob/...`. Ele não ajuda: no incidente típico os intermediários acumulados têm minutos ou poucas horas, e o sweeper não consulta o banco, de modo que, se alguém reduzir o limite de idade na linha de comando, ele apaga diretórios de trabalhos ativos que só estão lentos. O quarto equívoco é tratar a fila do RabbitMQ como sintoma primário. A fila `image-processor.trabalhos` cresce em qualquer degradação do serviço, inclusive quando o armazenamento de objetos está lento ou quando o `upload-gateway` reenvia um lote de imagens antigas. Antes de qualquer ação em disco, olhe a ocupação do volume. Se ela estiver abaixo de 70% e estável, o problema não é este runbook. O quinto ponto é o mais sutil: as métricas de ocupação são publicadas pela própria aplicação, a cada 15 segundos, e param de ser publicadas quando o contêiner está reiniciando. No painel, a linha parece estabilizar ou cair, quando na verdade há buraco de dados. Confirme sempre com `df` dentro do pod que está de pé. Por último, cuidado com o horário dos logs: os pods registram em UTC e o painel mostra horário local do navegador. Já houve ticket em que a linha do tempo ficou deslocada em três horas e a equipe associou o crescimento do disco a uma implantação que aconteceu depois.

## Verificação e escalonamento

A recuperação exige espaço livre estável, ausência de novos reinícios relacionados a disco e fila diminuindo de forma sustentada. Confira uma imagem de teste do início ao fim do fluxo, sem usar material de cliente. Registre o volume liberado, a quantidade de trabalhos preservados, a aprovação e as pendências de correção definitiva.

```bash
# Envia a imagem de teste do laboratório (arquivo sintético, sem dado de cliente)
kubectl -n midia exec image-processor-<hash>-<id> -c processor -- \
  imgproc-admin teste-ponta --amostra lab/xadrez-4000x3000.png --aguardar 120
```

Escalone para a equipe de mídia quando não for possível distinguir arquivos concluídos de ativos, quando a limpeza não liberar espaço ou quando a ocupação voltar a crescer no mesmo ritmo. Envie métricas, horários, versões implantadas e amostras sanitizadas. O post-mortem PM-041 descreve a falha anterior da rotina de limpeza, mas não serve como autorização para repetir a mesma remoção sem verificar o estado atual.

Outros caminhos: erro de publicação com volume abaixo de 70% vai para a equipe de plataforma (armazenamento de objetos); conexões recusadas no banco `midia_jobs` vão para a equipe de dados.
