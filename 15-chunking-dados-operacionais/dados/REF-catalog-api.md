# REF - catalog-api: configuração e operação

**Tipo:** referência
**Serviço:** catalog-api
**Equipe responsável:** catálogo (aplicação), plataforma (manifestos)
**Ambiente:** laboratório fictício da aula
**Versão de referência:** 3.13.2 (com notas para 3.14.x)

Este documento lista a configuração aceita pela catalog-api, os códigos de erro que aparecem nos logs e nas respostas, as rotas expostas e os manifestos Kubernetes de referência. Os valores padrão abaixo são os do artefato; os valores de produção vêm do ConfigMap `catalog-api-config` e do Secret `catalog-api-secrets`. Valores secretos aparecem aqui só como placeholder.

## Variáveis de ambiente

| Nome | Padrão | Descrição |
|---|---|---|
| `SERVER_PORT` | `8080` | Porta de tráfego HTTP. |
| `MANAGEMENT_SERVER_PORT` | `8081` | Porta do Actuator (probes e métricas). |
| `SERVER_TOMCAT_THREADS_MAX` | `200` | Threads de trabalho do Tomcat. |
| `SERVER_TOMCAT_ACCEPT_COUNT` | `100` | Fila de conexões aceitas antes de recusar. |
| `CATALOG_DB_URL` | nenhum | URL JDBC da réplica de leitura (`jdbc:postgresql://catalog-db-ro.dados.svc:5432/catalog`). |
| `CATALOG_DB_USER` | nenhum | Usuário de leitura. Vem do Secret. |
| `CATALOG_DB_PASSWORD` | nenhum | `<valor-no-gerenciador-de-segredos>` |
| `CATALOG_DB_POOL_MAX` | `10` | Tamanho máximo do pool HikariCP (produção usa 20). |
| `CATALOG_DB_POOL_CONNECTION_TIMEOUT_MS` | `1500` | Tempo máximo de espera por uma conexão do pool. |
| `CATALOG_DB_QUERY_TIMEOUT_MS` | `800` | Timeout por consulta. |
| `CATALOG_CACHE_REDIS_URL` | nenhum | Endereço do cluster `catalog-cache`. |
| `CATALOG_CACHE_REDIS_TIMEOUT_MS` | `50` | Timeout de comando no Redis. |
| `CATALOG_CACHE_L1_MAX_ENTRIES` | `50000` | Entradas máximas no Caffeine por pod. |
| `CATALOG_CACHE_L1_TTL_S` | `60` | TTL de produto no L1. |
| `CATALOG_CACHE_L2_TTL_S` | `600` | TTL de produto no Redis. |
| `CATALOG_CACHE_LISTING_TTL_S` | `120` | TTL de páginas de listagem. |
| `CATALOG_CACHE_OFFER_TTL_S` | `15` | TTL de ofertas no L1 (ofertas não vão ao L2). |
| `PRICING_BASE_URL` | nenhum | URL do pricing-service (`http://pricing-service.precos.svc:8080`). |
| `PRICING_CONNECT_TIMEOUT_MS` | `100` | Timeout de conexão com o pricing-service. |
| `PRICING_READ_TIMEOUT_MS` | `350` | Timeout de leitura com o pricing-service. |
| `PRICING_RETRY_MAX_ATTEMPTS` | `2` | Tentativas totais em erro de conexão (não se aplica a timeout). |
| `PRICING_CB_FAILURE_RATE_THRESHOLD` | `50` | Percentual de falha que abre o circuit breaker. |
| `PRICING_CB_SLIDING_WINDOW_SIZE` | `100` | Tamanho da janela deslizante, em chamadas. |
| `PRICING_CB_WAIT_OPEN_S` | `20` | Tempo com o circuito aberto antes de testar meio aberto. |
| `PRICING_BULKHEAD_MAX_CONCURRENT` | `40` | Chamadas simultâneas ao pricing-service por pod. |
| `PRICING_API_TOKEN` | nenhum | `<valor-no-gerenciador-de-segredos>` |
| `CATALOG_OFFERS_REGION_MAP` | nenhum | Mapa de sigla de região para código comercial, formato `SIGLA=CODIGO` separado por vírgula. Obrigatória a partir da 3.14.0. Ignorada pela 3.13.x. |
| `CATALOG_OFFERS_DEFAULT_REGION` | `SE` | Região usada quando a requisição não informa `region`. |
| `KAFKA_BOOTSTRAP_SERVERS` | nenhum | Brokers do cluster `lab-events`. |
| `KAFKA_CONSUMER_GROUP` | `catalog-api-cache-invalidator` | Grupo de consumo do tópico de invalidação. |
| `KAFKA_MAX_POLL_RECORDS` | `200` | Mensagens por lote. |
| `CATALOG_WARMUP_ENABLED` | `true` | Liga o job de pré-aquecimento do L2. |
| `CATALOG_WARMUP_TOP_N` | `5000` | Quantidade de produtos pré-aquecidos. |
| `CATALOG_WARMUP_CRON` | `0 */30 * * * *` | Agenda do job (sintaxe Spring, com segundos). |
| `LOGGING_LEVEL_ROOT` | `INFO` | Nível de log raiz (laboratório usa `DEBUG` em `lab.catalog`). |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | nenhum | Coletor OpenTelemetry do cluster. |
| `OTEL_RESOURCE_ATTRIBUTES` | nenhum | Inclui `service.version`, preenchido pelo pipeline. |
| `JAVA_TOOL_OPTIONS` | ver Deployment | Parâmetros da JVM e do agente OpenTelemetry. |

Observação sobre `CATALOG_OFFERS_REGION_MAP`: a sigla é a que o storefront-bff envia; o código é o do pricing-service. Exemplo do laboratório: `SUL=BR-R3,SE=BR-R1,NE=BR-R4,CO=BR-R2,N=BR-R5`. Siglas não mapeadas geram o erro `CAT-5031` na rota de oferta.

## Códigos de erro e mensagens de log

| Código | HTTP | Mensagem de log típica | Observação |
|---|---|---|---|
| `CAT-4001` | 400 | `Parâmetro region inválido: <valor>` | Região fora do formato de sigla. |
| `CAT-4041` | 404 | `Produto não encontrado sku=<sku>` | Também ocorre com SKU inativo. |
| `CAT-4290` | 429 | `Limite de requisições excedido para cliente=<id>` | Só para clientes internos sem isenção. |
| `CAT-5001` | 500 | `Erro inesperado ao processar requisição` | Tratador global; ver `exception`. |
| `CAT-5031` | 500 | `Falha ao resolver oferta sku=<sku> region=<sigla>` | Resolvedor de ofertas sem mapeamento ou não inicializado. |
| `CAT-5032` | 500 | `Resolvedor de ofertas indisponível` | Inicialização anterior falhou; o componente não tenta de novo até reiniciar. |
| `CAT-5030` | 503 | `Réplica de catálogo indisponível` | Timeout ou recusa de conexão no PostgreSQL. |
| `CAT-5033` | 503 | `Pool de conexões esgotado (pending=<n>)` | Espera maior que `CATALOG_DB_POOL_CONNECTION_TIMEOUT_MS`. |
| `CAT-5034` | 503 | `Bulkhead de preços cheio` | Mais de `PRICING_BULKHEAD_MAX_CONCURRENT` chamadas simultâneas. |
| sem código | 200 | `Circuito de preços aberto, oferta sem preço sku=<sku>` | Resposta degradada com `priceStatus=UNAVAILABLE`. |
| sem código | não se aplica | `Partições revogadas` / `Partições atribuídas` | Rebalanceamento do consumidor, esperado em implantação. |
| sem código | não se aplica | `Cache miss em massa no L1` | Esperado após início de pod. |

As respostas de erro seguem o formato `application/problem+json` com os campos `type`, `title`, `status`, `code` e `traceId`. O campo `detail` é omitido em produção para não vazar SKU de cliente ou parâmetro interno.

## Rotas e filas

| Rota ou fila | Método ou papel | Descrição |
|---|---|---|
| `/v1/products/{sku}` | GET | Produto, navegação. |
| `/v1/products/{sku}/offers` | GET | Oferta com preço e disponibilidade; parâmetro `region`. |
| `/v1/offers:batch` | POST | Oferta em lote, até 50 SKUs por chamada. |
| `/v1/listings` | GET | Listagem paginada com filtros; `page_size` máximo 60. |
| `/v1/categories/{id}/products` | GET | Produtos de uma categoria. |
| `/actuator/health/liveness` | GET (8081) | Liveness. |
| `/actuator/health/readiness` | GET (8081) | Readiness, inclui banco, Redis e resolvedor de ofertas. |
| `/actuator/prometheus` | GET (8081) | Métricas. |
| `catalog.product-updated` | tópico Kafka, consumo | Invalidação de cache, 12 partições. |
| `catalog:l1-evict` | canal pub/sub Redis | Invalidação de L1 entre pods. |
| `catalog:warmup-lock` | chave Redis | Lock do job de pré-aquecimento, expira em 25 min. |

## Limites de recursos

| Item | Valor |
|---|---|
| CPU (request / limit) | 1 / 2 vCPU |
| Memória (request / limit) | 2 GiB / 2,5 GiB |
| Heap JVM | `-Xms1536m -Xmx1536m` |
| Réplicas (mín. / máx.) | 6 / 16 |
| Conexões de banco por pod | 20 |
| Tempo de encerramento gracioso | 45 s (`terminationGracePeriodSeconds`) |
| Atraso de pre-stop | 10 s |

## Deployment de referência

```yaml
# Deployment da catalog-api no namespace catalogo (gerado pelo pipeline; não editar à mão no cluster)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: catalog-api
  namespace: catalogo
  labels:
    app: catalog-api
    equipe: catalogo
spec:
  replicas: 6
  revisionHistoryLimit: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: catalog-api
  template:
    metadata:
      labels:
        app: catalog-api
      annotations:
        prometheus.io/port: "8081"
        checksum/config: "<preenchido-pelo-pipeline>"
    spec:
      serviceAccountName: catalog-api
      terminationGracePeriodSeconds: 45
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app: catalog-api
      containers:
        - name: catalog-api
          image: registry.lab.example/catalogo/catalog-api:3.13.2
          ports:
            - name: http
              containerPort: 8080
            - name: management
              containerPort: 8081
          envFrom:
            - configMapRef:
                name: catalog-api-config
            - secretRef:
                name: catalog-api-secrets
          env:
            - name: JAVA_TOOL_OPTIONS
              value: >-
                -Xms1536m -Xmx1536m -XX:+UseG1GC -XX:MaxGCPauseMillis=150
                -javaagent:/otel/opentelemetry-javaagent.jar
          resources:
            requests:
              cpu: "1"
              memory: 2Gi
            limits:
              cpu: "2"
              memory: 2560Mi
          startupProbe:
            httpGet:
              path: /actuator/health/liveness
              port: management
            periodSeconds: 5
            failureThreshold: 24
          readinessProbe:
            httpGet:
              path: /actuator/health/readiness
              port: management
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 3
          livenessProbe:
            httpGet:
              path: /actuator/health/liveness
              port: management
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 6
          lifecycle:
            preStop:
              exec:
                command: ["sh", "-c", "sleep 10"]
```

## HorizontalPodAutoscaler

```yaml
# HPA por CPU e requisições por pod; o maior dos dois vence
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: catalog-api
  namespace: catalogo
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: catalog-api
  minReplicas: 6
  maxReplicas: 16
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 65
    - type: Pods
      pods:
        metric:
          name: http_server_requests_per_second
        target:
          type: AverageValue
          averageValue: "180"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
```

## ConfigMap

```yaml
# valores não secretos; o mapa de regiões entrou depois do PM-021
apiVersion: v1
kind: ConfigMap
metadata:
  name: catalog-api-config
  namespace: catalogo
data:
  CATALOG_DB_URL: "jdbc:postgresql://catalog-db-ro.dados.svc:5432/catalog"
  CATALOG_DB_POOL_MAX: "20"
  CATALOG_CACHE_REDIS_URL: "redis://catalog-cache.dados.svc:6379"
  PRICING_BASE_URL: "http://pricing-service.precos.svc:8080"
  PRICING_READ_TIMEOUT_MS: "350"
  CATALOG_OFFERS_REGION_MAP: "SUL=BR-R3,SE=BR-R1,NE=BR-R4,CO=BR-R2,N=BR-R5"
  KAFKA_BOOTSTRAP_SERVERS: "kafka-0.lab-events.svc:9092,kafka-1.lab-events.svc:9092"
  LOGGING_LEVEL_LAB_CATALOG: "DEBUG"
  OTEL_EXPORTER_OTLP_ENDPOINT: "http://otel-collector.observabilidade.svc:4317"
```

## PodDisruptionBudget

```yaml
# garante capacidade mínima durante drenagem de nós
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: catalog-api
  namespace: catalogo
spec:
  minAvailable: 5
  selector:
    matchLabels:
      app: catalog-api
```

O PDB com `minAvailable: 5` foi escolhido para permitir a drenagem de um nó por vez com o mínimo de 6 réplicas. Se o HPA estiver no mínimo e houver um pod sem prontidão, a drenagem de nós fica bloqueada; isso já atrasou uma janela de manutenção do cluster e é o comportamento desejado.

## Operação do dia a dia

Comandos frequentes, todos no namespace `catalogo`:

```bash
# reinício controlado (respeita maxUnavailable: 0)
kubectl -n catalogo rollout restart deploy/catalog-api

# conferir o valor efetivo de uma variável num pod
kubectl -n catalogo exec deploy/catalog-api -- printenv PRICING_READ_TIMEOUT_MS

# estado do circuit breaker de preços
kubectl -n catalogo exec deploy/catalog-api -- \
  curl -s localhost:8081/actuator/circuitbreakers | head -50

# atraso do grupo de consumo
kubectl -n lab-events exec kafka-0 -- kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --describe --group catalog-api-cache-invalidator
```

Mudanças em ConfigMap não são lidas a quente; é preciso reiniciar o Deployment. O pipeline faz isso automaticamente quando o hash do ConfigMap muda, pela anotação `checksum/config` no template do pod. Mudanças feitas à mão no cluster são sobrescritas na próxima sincronização do ArgoCD.
