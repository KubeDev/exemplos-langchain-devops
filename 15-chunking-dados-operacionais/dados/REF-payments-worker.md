# REF - payments-worker: configuração e operação

**Tipo:** referência
**Serviço:** payments-worker
**Equipe responsável:** pagamentos
**Ambiente:** laboratório fictício da aula
**Versão de referência:** 2.18.3

## Como usar esta referência

Este documento lista a configuração efetiva do payments-worker no laboratório: variáveis de ambiente, mensagens de log com código, filas e endpoints, limites de recursos e os manifestos aplicados no namespace `pagamentos`. Os valores aqui são os padrões da imagem ou os definidos no ConfigMap; quando o ConfigMap sobrescreve o padrão da imagem, as duas colunas aparecem na tabela. Valores de segredos nunca aparecem: onde é preciso ilustrar, usa-se `<valor-no-gerenciador-de-segredos>`.

Mudanças em qualquer valor desta página exigem ticket de mudança (CHG) com a justificativa e, para parâmetros de consumo (prefetch, threads, tentativas), teste de carga anexado.

## Variáveis de ambiente

| Nome | Padrão da imagem | Valor no laboratório | Descrição |
|---|---|---|---|
| `PW_PROFILE` | `default` | `lab` | Perfil Spring ativo. |
| `PW_LOG_LEVEL` | `INFO` | `DEBUG` | Nível de log raiz. O laboratório usa DEBUG para fins didáticos. |
| `PW_LOG_FORMAT` | `json` | `json` | Formato de saída de log. `text` só para desenvolvimento local. |
| `BROKER_HOSTS` | (vazio) | `broker-0.mensageria:5671,broker-1.mensageria:5671,broker-2.mensageria:5671` | Lista de nós do broker, TLS obrigatório. |
| `BROKER_VHOST` | `/` | `pagamentos` | Vhost do broker. |
| `BROKER_CREDENTIAL_FILE` | `/var/run/secrets/broker/credencial` | igual | Arquivo com usuário e senha, lido apenas na inicialização do processo. |
| `BROKER_CONNECTION_TIMEOUT_MS` | `10000` | igual | Tempo máximo do handshake. |
| `BROKER_HEARTBEAT_S` | `30` | igual | Intervalo de heartbeat AMQP. |
| `BROKER_CONNECTION_MAX_LIFETIME` | `0` (desligado) | `15m` | Tempo máximo de vida da conexão antes da renovação periódica. |
| `BROKER_CONNECTION_JITTER` | `0s` | `90s` | Desvio aleatório somado ao tempo máximo de vida, por pod. |
| `BROKER_RECONNECT_MAX_ATTEMPTS` | `5` | igual | Tentativas de reconexão antes de o consumidor desistir do canal. |
| `BROKER_RECONNECT_INITIAL_BACKOFF_MS` | `1000` | igual | Primeiro intervalo de backoff, dobra a cada tentativa. |
| `BROKER_RECOVERY_INTERVAL` | `60s` | igual | Intervalo do ciclo de recuperação automática depois que as tentativas se esgotam. |
| `CONSUMER_QUEUE` | `pagamentos.cobranca.v2` | igual | Fila consumida. |
| `CONSUMER_THREADS` | `4` | `8` | Threads consumidoras (um canal por thread). |
| `CONSUMER_PREFETCH` | `25` | igual | Mensagens não confirmadas por canal. Era 40 até a versão 2.17. |
| `PAY_MAX_ATTEMPTS` | `4` | igual | Tentativas com nack/requeue antes do envio à quarentena. |
| `PAY_ACK_TIMEOUT_MS` | `45000` | igual | Tempo máximo entre a entrega e o ack; acima disso a thread registra PW-214. |
| `RESULT_EXCHANGE` | `pedidos.resultado` | igual | Exchange de publicação de resultado. |
| `RESULT_CONFIRM_TIMEOUT_MS` | `5000` | igual | Espera pelo publisher confirm. |
| `GATEWAY_URL` | (vazio) | `http://card-gateway-sim.pagamentos:8080` | Endereço do gateway simulado. |
| `GATEWAY_TIMEOUT_MS` | `4000` | igual | Timeout por chamada ao gateway. |
| `GATEWAY_WARN_LATENCY_MS` | `2000` | igual | Acima disso, log WARN de latência (não altera o fluxo). |
| `GATEWAY_POOL_MAX` | `64` | igual | Conexões HTTP máximas no pool. |
| `GATEWAY_POOL_PER_ROUTE` | `32` | igual | Conexões por rota. |
| `GATEWAY_CB_FAILURE_RATE` | `50` | igual | Percentual de falha para abrir o circuit breaker. |
| `GATEWAY_CB_WINDOW` | `20` | igual | Tamanho da janela (chamadas) do circuit breaker. |
| `GATEWAY_CB_OPEN_DURATION` | `30s` | igual | Tempo com o circuito aberto antes do meio aberto. |
| `IDEM_REDIS_URL` | (vazio) | `redis://payments-idem.pagamentos:6379/0` | Armazenamento de idempotência. |
| `IDEM_TTL` | `72h` | igual | TTL das chaves de idempotência. |
| `IDEM_REDIS_TIMEOUT_MS` | `300` | igual | Timeout por operação no Redis. |
| `IDEM_WARN_LATENCY_MS` | `150` | igual | Acima disso, log WARN de latência do Redis. |
| `SHUTDOWN_DRAIN_TIMEOUT` | `25s` | igual | Espera pelas mensagens em voo após SIGTERM. |
| `STATS_INTERVAL` | `60s` | igual | Intervalo da linha de estatísticas do consumidor. |
| `ADMIN_TOKEN_FILE` | `/var/run/secrets/admin/token` | igual | Token de serviço exigido pelos endpoints `/admin`. |
| `LEGACY_FIELD_WARN` | `true` | igual | Emite WARN ao encontrar o campo `moeda_codigo`. |
| `JAVA_TOOL_OPTIONS` | (vazio) | `-XX:MaxRAMPercentage=70 -XX:+UseG1GC -Xlog:gc:none` | Opções da JVM. |

## Códigos de erro e mensagens de log

Os códigos aparecem no campo `message` entre colchetes apenas no perfil `prod`; no perfil `lab` a mensagem sai sem o código, mas o texto é o mesmo. A tabela serve para buscar no código e na documentação.

| Código | Nível | Mensagem (início) | Significado |
|---|---|---|---|
| PW-101 | INFO | `conexão com broker atingiu tempo máximo de vida, renovando` | Renovação periódica iniciada. |
| PW-102 | WARN | `renovação de conexão recusada pelo broker` | Handshake recusado em uma tentativa de reconexão. Inclui o motivo informado pelo broker. |
| PW-103 | ERROR | `consumidor ... sem conexão após N tentativas` | Tentativas esgotadas; consumidor parado até o próximo ciclo de recuperação. |
| PW-104 | WARN | `recuperação automática: handshake recusado` | Ciclo de recuperação falhou. |
| PW-105 | INFO | `conectado ao broker nó` | Conexão estabelecida. |
| PW-110 | INFO | `credencial do broker carregada de` | Leitura do arquivo de credencial na inicialização; registra a anotação de versão, nunca o valor. |
| PW-201 | INFO | `cobrança processada` | Fluxo completo com ack. |
| PW-202 | INFO | `cobrança já processada, republicando resultado armazenado` | Reentrega com estado final no Redis; o resultado é publicado de novo sem chamar o gateway. |
| PW-210 | ERROR | `falha ao publicar resultado` | Publicação falhou; a mensagem não é confirmada e será reentregue. |
| PW-211 | ERROR | `ack falhou` | Canal fechado no momento do ack. |
| PW-214 | WARN | `ack acima do tempo limite` | Processamento passou de `PAY_ACK_TIMEOUT_MS`. |
| PW-220 | WARN | `mensagem enviada à quarentena` | Esgotou `PAY_MAX_ATTEMPTS`. |
| PW-301 | WARN | `latência do gateway acima do limite de aviso` | Somente informativo. |
| PW-302 | ERROR | `circuit breaker do gateway aberto` | Chamadas ao gateway suspensas por `GATEWAY_CB_OPEN_DURATION`. |
| PW-401 | WARN | `redis payments-idem respondeu em` | Latência acima de `IDEM_WARN_LATENCY_MS`. |
| PW-402 | ERROR | `redis payments-idem indisponível` | Readiness passa a falhar. |
| PW-501 | WARN | `mensagem contém campo legado 'moeda_codigo'` | Campo ignorado; ver DT-12 na arquitetura. |
| PW-601 | WARN | `pausa de GC acima de 200ms` | Pausa longa de coleta; investigar só se recorrente. |

## Filas, exchanges e endpoints

| Recurso | Tipo | Detalhe |
|---|---|---|
| `pagamentos.cobranca` | exchange topic | Publicada pela orders-api, routing keys `cobranca.criada` e `estorno.criado`. |
| `pagamentos.cobranca.v2` | fila quorum | Consumida pelo worker. Política `pagamentos-limite`: `max-length` 500000, `overflow` reject-publish. |
| `pagamentos.cobranca.quarentena` | fila clássica | Recebe da DLX `pagamentos.dlx`; TTL de mensagem 14 dias. |
| `pagamentos.cobranca.v1` | fila clássica | Sem tráfego, mantida por relatório legado. |
| `pedidos.resultado` | exchange topic | Routing keys `pagamento.aprovado`, `pagamento.recusado`, `pagamento.erro`. |
| `GET /health/live` | HTTP 8080 | Retorna 200 se a JVM responde. |
| `GET /health/ready` | HTTP 8080 | Verifica servidor HTTP e Redis de idempotência. Não verifica o broker. |
| `GET /metrics` | HTTP 8080 | Métricas Prometheus. |
| `GET /admin/info` | HTTP 8080 | Versão, horário de início do processo, threads. Exige token de serviço. |
| `POST /admin/consumo/pausar` | HTTP 8080 | Cancela os consumidores sem encerrar o processo. Exige token. |
| `POST /admin/consumo/retomar` | HTTP 8080 | Recria os consumidores na conexão existente. Não relê a credencial. |

O endpoint `/admin/consumo/retomar` costuma ser tentado em incidentes de conexão, mas ele reaproveita a fábrica de conexões do processo, com a mesma credencial carregada na inicialização. Ele só ajuda quando a falha é de canal, não de autenticação.

## Limites de recursos e capacidade

| Item | Valor |
|---|---|
| CPU request / limit | `500m` / `1500m` |
| Memória request / limit | `768Mi` / `1Gi` |
| Heap efetivo (70% do limite) | cerca de 716 MiB |
| Réplicas HPA | mínimo 2, máximo 8 |
| Alvo de CPU do HPA | 65% |
| Estabilização de redução do HPA | 300 s |
| `terminationGracePeriodSeconds` | 30 |
| Throughput por pod (8 threads) | 14 a 30 mensagens/s |
| Conexões AMQP por pod | 1 (8 canais) |
| Conexões AMQP permitidas ao usuário `svc-payments-worker` | 20 (limite definido pela mensageria) |

O limite de 20 conexões por usuário no broker é relevante durante reinícios: com 8 réplicas e um `rollout restart` com surge de 25%, o pico pode chegar a 10 conexões, ainda dentro do limite. O limite foi atingido uma vez quando um teste de carga subiu 16 réplicas manualmente, e as réplicas excedentes ficaram em loop de PW-102 com motivo `connection_limit`.

## Manifestos

### Deployment

```yaml
# Deployment aplicado no laboratório (trecho completo, sem o Secret)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payments-worker
  namespace: pagamentos
  labels:
    app: payments-worker
    equipe: pagamentos
spec:
  replicas: 2
  revisionHistoryLimit: 5
  selector:
    matchLabels:
      app: payments-worker
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: payments-worker
      annotations:
        pagamentos.lab/secret-versao: payments-broker-cred-v14
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
    spec:
      serviceAccountName: payments-worker
      terminationGracePeriodSeconds: 30
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        fsGroup: 10001
      containers:
        - name: worker
          image: registro.lab.interno/pagamentos/payments-worker:2.18.3
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 8080
          envFrom:
            - configMapRef:
                name: payments-worker-config
          resources:
            requests:
              cpu: 500m
              memory: 768Mi
            limits:
              cpu: 1500m
              memory: 1Gi
          readinessProbe:
            httpGet:
              path: /health/ready
              port: http
            periodSeconds: 10
            failureThreshold: 3
          livenessProbe:
            httpGet:
              path: /health/live
              port: http
            initialDelaySeconds: 30
            periodSeconds: 20
            failureThreshold: 3
          securityContext:
            readOnlyRootFilesystem: true
            allowPrivilegeEscalation: false
            capabilities:
              drop: ["ALL"]
          volumeMounts:
            - name: broker-cred
              mountPath: /var/run/secrets/broker
              readOnly: true
            - name: admin-token
              mountPath: /var/run/secrets/admin
              readOnly: true
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: broker-cred
          secret:
            secretName: payments-broker-cred
        - name: admin-token
          secret:
            secretName: payments-worker-admin
        - name: tmp
          emptyDir:
            sizeLimit: 256Mi
```

A anotação `pagamentos.lab/secret-versao` é apenas informativa: ela não força reinício quando o Secret muda, porque o operador de sincronização atualiza o Secret `payments-broker-cred` sem alterar o template. Ela é atualizada manualmente no mesmo CHG da rotação.

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: payments-worker-config
  namespace: pagamentos
data:
  PW_PROFILE: "lab"
  PW_LOG_LEVEL: "DEBUG"
  BROKER_HOSTS: "broker-0.mensageria:5671,broker-1.mensageria:5671,broker-2.mensageria:5671"
  BROKER_VHOST: "pagamentos"
  BROKER_CONNECTION_MAX_LIFETIME: "15m"
  BROKER_CONNECTION_JITTER: "90s"
  CONSUMER_THREADS: "8"
  GATEWAY_URL: "http://card-gateway-sim.pagamentos:8080"
  IDEM_REDIS_URL: "redis://payments-idem.pagamentos:6379/0"
  JAVA_TOOL_OPTIONS: "-XX:MaxRAMPercentage=70 -XX:+UseG1GC -Xlog:gc:none"
```

### HorizontalPodAutoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: payments-worker
  namespace: pagamentos
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: payments-worker
  minReplicas: 2
  maxReplicas: 8
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 65
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
```

### PodDisruptionBudget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: payments-worker
  namespace: pagamentos
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: payments-worker
```

O PDB protege contra drenagem de nó, não contra `kubectl delete pod`. Durante o reinício em lotes do RB-381 o PDB não impede o operador de apagar os dois pods ao mesmo tempo; a disciplina de um pod por vez é do procedimento.

### Secret (formato)

```yaml
# Formato do Secret sincronizado pelo operador; o valor real fica no gerenciador de segredos
apiVersion: v1
kind: Secret
metadata:
  name: payments-broker-cred
  namespace: pagamentos
  annotations:
    sincronizacao.lab/origem: pagamentos/broker/svc-payments-worker
    sincronizacao.lab/versao: "14"
type: Opaque
stringData:
  credencial: "usuario=svc-payments-worker;senha=<valor-no-gerenciador-de-segredos>"
```

## Comandos úteis

```bash
# Versão e início do processo de cada pod (exige token de serviço montado no pod)
for p in $(kubectl -n pagamentos get pods -l app=payments-worker -o name); do
  kubectl -n pagamentos exec "$p" -- sh -c 'curl -s -H "Authorization: Bearer $(cat /var/run/secrets/admin/token)" localhost:8080/admin/info'
done

# Gauge de conexão ao broker por pod
kubectl -n pagamentos exec deploy/payments-worker -- curl -s localhost:8080/metrics | grep pw_broker_connected
```

```promql
# Pods sem conexão ao broker (a métrica existe, o alerta ainda não)
min by (pod) (pw_broker_connected{namespace="pagamentos"}) == 0
```

## Métricas expostas

`pw_messages_processed_total{resultado}`, `pw_gateway_latency_seconds` (histograma), `pw_redeliveries_total`, `pw_idempotency_discards_total`, `pw_gateway_circuit_state` (0 fechado, 1 meio aberto, 2 aberto), `pw_broker_connected`, `pw_inflight_messages`, `pw_quarantine_sent_total`. Todas com os rótulos `pod` e `namespace` adicionados pela coleta.
