# REF - image-processor: configuração e operação

**Tipo:** referência
**Serviço:** image-processor
**Equipe responsável:** mídia
**Ambiente:** laboratório fictício da aula

Este documento lista a configuração do image-processor como está no repositório de implantação do laboratório. Valores mudam com frequência em preparação de campanha; quando houver divergência entre este documento e o ConfigMap aplicado no cluster, vale o cluster, e este documento deve ser corrigido.

## Variáveis de ambiente

| Nome | Padrão | Descrição |
|---|---|---|
| `IMGPROC_LOG_LEVEL` | `INFO` | Nível de log. `DEBUG` é ligado em um pod por vez para amostragem. |
| `IMGPROC_AMQP_URL` | `<valor-no-gerenciador-de-segredos>` | URL de conexão com o RabbitMQ, injetada a partir de Secret. |
| `IMGPROC_QUEUE` | `image-processor.trabalhos` | Fila consumida. |
| `IMGPROC_PREFETCH` | `4` | Mensagens não confirmadas por pod; equivale a trabalhos simultâneos. |
| `IMGPROC_MAX_REDELIVERIES` | `3` | Reentregas antes de rejeitar para a DLQ. |
| `IMGPROC_SCRATCH_DIR` | `/scratch` | Raiz do volume temporário. |
| `IMGPROC_SCRATCH_RESERVE_MB` | `512` | Espaço livre mínimo para aceitar trabalho novo; abaixo disso o consumidor recusa e devolve a mensagem. |
| `IMGPROC_QUARANTINE_TTL_HOURS` | `72` | Retenção de `/scratch/quarentena/`. |
| `IMGPROC_SCRATCH_REPORT_INTERVAL_S` | `120` | Intervalo da linha de log com o uso do volume. |
| `IMGPROC_MAX_MEGAPIXELS` | `80` | Limite de resolução aceito na entrada. |
| `IMGPROC_VERIFY_FULL_TIMEOUT_MS` | `2500` | Tempo máximo da verificação completa antes de passar à verificação por amostragem. |
| `IMGPROC_VERIFY_PHASH_MAX_DISTANCE` | `6` | Distância máxima de hash perceptual aceita (WebP e JPEG). |
| `IMGPROC_VERIFY_PHASH_MAX_DISTANCE_AVIF` | `9` | Distância máxima aceita para AVIF. |
| `IMGPROC_VARIANTS` | `thumb:160,card:480,detalhe:1200,zoom:2400` | Variantes geradas e largura em pixels. |
| `IMGPROC_AVIF_VARIANTS` | `detalhe,zoom` | Variantes que também recebem AVIF. |
| `IMGPROC_AVIF_SPEED` | `7` | Velocidade do codificador AVIF (0 a 9, maior é mais rápido). |
| `IMGPROC_WEBP_QUALITY` | `82` | Qualidade WebP. |
| `IMGPROC_OBJ_ENDPOINT` | `http://objetos-lab.plataforma.svc:9000` | Endpoint do armazenamento de objetos. |
| `IMGPROC_OBJ_READ_TIMEOUT_S` | `30` | Timeout de leitura do original. |
| `IMGPROC_OBJ_MULTIPART_THRESHOLD_MB` | `8` | Tamanho a partir do qual o upload usa multipart. |
| `IMGPROC_DB_DSN` | `<valor-no-gerenciador-de-segredos>` | DSN do PostgreSQL `midia_jobs`. |
| `IMGPROC_DB_POOL_SIZE` | `6` | Conexões por pod. |
| `IMGPROC_DB_STATEMENT_TIMEOUT_MS` | `2000` | Timeout por consulta. |
| `IMGPROC_REDIS_URL` | `redis://midia-cache.midia.svc:6379/2` | Redis de idempotência. |
| `IMGPROC_REDIS_TIMEOUT_MS` | `300` | Timeout de operação no Redis. |
| `IMGPROC_IDEMPOTENCY_TTL_S` | `86400` | TTL da chave `imgproc:idem:<job_id>`. |
| `VIPS_CONCURRENCY` | `2` | Threads internas da libvips por operação. |
| `VIPS_CACHE_MAX_MEM_MB` | `100` | Cache de operações da libvips. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://otel-coletor.observabilidade.svc:4317` | Coletor de traces. |
| `OTEL_TRACES_SAMPLER_ARG` | `0.2` | Fração de traces amostrados. |

## Endpoints e filas

| Recurso | Tipo | Detalhe |
|---|---|---|
| `GET /healthz/live` | HTTP 8081 | Grava e lê `/scratch/.probe`; falha se a escrita falhar. |
| `GET /healthz/ready` | HTTP 8081 | Pronto quando conectado ao broker e ao banco. |
| `GET /metrics` | HTTP 8081 | Métricas Prometheus. |
| `POST /admin/consumo` | HTTP 8081 | Pausa, retoma e ajusta `prefetch`. Usado por `imgproc-admin consumo`. |
| `GET /admin/scratch-report` | HTTP 8081 | Cruzamento diretório x estado, somente leitura. |
| `POST /admin/scratch-limpar` | HTTP 8081 | Remove diretórios de uma lista, recusando estado alterado. |
| `midia.eventos` | exchange topic | Entrada `imagem.recebida`, saída `imagem.publicada`. |
| `image-processor.trabalhos` | fila durável | `x-dead-letter-exchange` para a DLQ, `x-max-length` 200000. |
| `image-processor.trabalhos.dlq` | fila durável | Retenção de 7 dias (`x-message-ttl` 604800000). |

As rotas `/admin/*` só respondem a requisições originadas de dentro do pod (`127.0.0.1`); o `imgproc-admin` roda via `kubectl exec`.

## Códigos de erro e mensagens de log

| Código | Nível | Mensagem típica | Observação |
|---|---|---|---|
| `IMG-E101` | ERROR | `formato não suportado: <tipo>` | Vai direto para a DLQ. |
| `IMG-E102` | ERROR | `resolução acima do limite: <mp> MP` | Limite em `IMGPROC_MAX_MEGAPIXELS`. |
| `IMG-E110` | WARN | `leitura do original lenta: <ms> ms` | Acima de 10 s; não falha o trabalho. |
| `IMG-E111` | ERROR | `timeout ao ler original` | Recuperável, mensagem devolvida. |
| `IMG-E120` | ERROR | `falha de escrita em /scratch: [Errno 28] No space left on device` | Trabalho vai para `falhou`. |
| `IMG-E121` | WARN | `espaço livre em /scratch abaixo da reserva` | Consumidor devolve a mensagem sem processar. |
| `IMG-E122` | WARN | `falha ao remover diretório do trabalho` | Conta em `imgproc_cleanup_failures_total`. |
| `IMG-E130` | WARN | `verificação completa excedeu <ms> ms, usando amostragem` | Informativo desde 4.18.0. |
| `IMG-E131` | ERROR | `variante reprovada na verificação: <variante>` | Trabalho vai para `falhou`. |
| `IMG-E140` | ERROR | `falha ao publicar variante` | Recuperável até 3 tentativas. |
| `IMG-E150` | WARN | `redis indisponível, seguindo sem idempotência` | Esperado em manutenção do Redis. |
| `IMG-E160` | ERROR | `sonda de vivacidade falhou: <motivo>` | Antecede reinício do contêiner. |

O código aparece no campo `message` entre colchetes no início da linha somente a partir da 4.19.0. Em versões anteriores, a busca precisa ser feita pelo texto da mensagem.

## Limites de recursos

| Recurso | Request | Limit |
|---|---|---|
| CPU (`processor`) | 1500m | 2000m |
| Memória (`processor`) | 2Gi | 4Gi |
| Volume `scratch` | 10Gi (PVC efêmero) | 10Gi |
| Armazenamento efêmero do contêiner (raiz) | 256Mi | 1Gi |

Cota do namespace `midia` para volumes efêmeros somados: 120Gi. Classe de armazenamento do volume: `lab-ssd`.

## Deployment

O manifesto abaixo é a versão aplicada no laboratório, sem os rótulos de controle da esteira.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: image-processor
  namespace: midia
  labels:
    app: image-processor
    equipe: midia
spec:
  replicas: 3
  revisionHistoryLimit: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: image-processor
  template:
    metadata:
      labels:
        app: image-processor
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8081"
    spec:
      serviceAccountName: image-processor
      terminationGracePeriodSeconds: 120
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        fsGroup: 10001
      containers:
        - name: processor
          image: registry.lab.local/midia/image-processor:4.19.0
          ports:
            - name: admin
              containerPort: 8081
          envFrom:
            - configMapRef:
                name: image-processor-config
          env:
            - name: IMGPROC_AMQP_URL
              valueFrom:
                secretKeyRef:
                  name: image-processor-secrets
                  key: amqp-url
            - name: IMGPROC_DB_DSN
              valueFrom:
                secretKeyRef:
                  name: image-processor-secrets
                  key: db-dsn
          resources:
            requests:
              cpu: 1500m
              memory: 2Gi
              ephemeral-storage: 256Mi
            limits:
              cpu: 2000m
              memory: 4Gi
              ephemeral-storage: 1Gi
          livenessProbe:
            httpGet:
              path: /healthz/live
              port: admin
            periodSeconds: 20
            timeoutSeconds: 3
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /healthz/ready
              port: admin
            periodSeconds: 10
            failureThreshold: 2
          lifecycle:
            preStop:
              exec:
                command: ["imgproc-admin", "consumo", "--pausar"]
          volumeMounts:
            - name: scratch
              mountPath: /scratch
      volumes:
        - name: scratch
          ephemeral:
            volumeClaimTemplate:
              metadata:
                labels:
                  app: image-processor
              spec:
                accessModes: ["ReadWriteOnce"]
                storageClassName: lab-ssd
                resources:
                  requests:
                    storage: 10Gi
```

Com `periodSeconds: 20` e `failureThreshold: 3`, um volume cheio leva cerca de 60 segundos entre a primeira falha de escrita da sonda e o reinício do contêiner.

## ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: image-processor-config
  namespace: midia
data:
  IMGPROC_LOG_LEVEL: "INFO"
  IMGPROC_QUEUE: "image-processor.trabalhos"
  IMGPROC_PREFETCH: "4"
  IMGPROC_MAX_REDELIVERIES: "3"
  IMGPROC_SCRATCH_DIR: "/scratch"
  IMGPROC_SCRATCH_RESERVE_MB: "512"
  IMGPROC_QUARANTINE_TTL_HOURS: "72"
  IMGPROC_SCRATCH_REPORT_INTERVAL_S: "120"
  IMGPROC_MAX_MEGAPIXELS: "80"
  IMGPROC_VERIFY_FULL_TIMEOUT_MS: "2500"
  IMGPROC_VERIFY_PHASH_MAX_DISTANCE: "6"
  IMGPROC_VERIFY_PHASH_MAX_DISTANCE_AVIF: "9"
  IMGPROC_VARIANTS: "thumb:160,card:480,detalhe:1200,zoom:2400"
  IMGPROC_AVIF_VARIANTS: "detalhe,zoom"
  IMGPROC_AVIF_SPEED: "7"
  IMGPROC_WEBP_QUALITY: "82"
  IMGPROC_OBJ_ENDPOINT: "http://objetos-lab.plataforma.svc:9000"
  IMGPROC_OBJ_READ_TIMEOUT_S: "30"
  IMGPROC_OBJ_MULTIPART_THRESHOLD_MB: "8"
  IMGPROC_DB_POOL_SIZE: "6"
  IMGPROC_DB_STATEMENT_TIMEOUT_MS: "2000"
  IMGPROC_REDIS_URL: "redis://midia-cache.midia.svc:6379/2"
  IMGPROC_REDIS_TIMEOUT_MS: "300"
  IMGPROC_IDEMPOTENCY_TTL_S: "86400"
  VIPS_CONCURRENCY: "2"
  VIPS_CACHE_MAX_MEM_MB: "100"
  OTEL_EXPORTER_OTLP_ENDPOINT: "http://otel-coletor.observabilidade.svc:4317"
  OTEL_TRACES_SAMPLER_ARG: "0.2"
```

## HorizontalPodAutoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: image-processor
  namespace: midia
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: image-processor
  minReplicas: 3
  maxReplicas: 8
  metrics:
    - type: External
      external:
        metric:
          name: rabbitmq_queue_messages_ready
          selector:
            matchLabels:
              queue: image-processor.trabalhos
        target:
          type: AverageValue
          averageValue: "40"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0
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

## PodDisruptionBudget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: image-processor
  namespace: midia
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: image-processor
```

## CronJob do sweeper

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: image-processor-tmp-sweeper
  namespace: midia
spec:
  schedule: "30 3 * * *"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 2
  failedJobsHistoryLimit: 5
  jobTemplate:
    spec:
      backoffLimit: 0
      template:
        spec:
          serviceAccountName: image-processor-sweeper
          restartPolicy: Never
          containers:
            - name: sweeper
              image: registry.lab.local/plataforma/kubectl:1.30
              args:
                - /bin/sh
                - -c
                - |
                  # remove diretórios de trabalho com mais de 24h em cada pod
                  for p in $(kubectl -n midia get pods -l app=image-processor -o name); do
                    kubectl -n midia exec "$p" -c processor -- \
                      find /scratch/jobs -mindepth 1 -maxdepth 1 -type d -mmin +1440 -exec rm -rf {} +
                  done
```

## Comandos `imgproc-admin`

- `imgproc-admin consumo --pausar | --retomar | --prefetch <n>`: controla o consumidor do pod local.
- `imgproc-admin scratch-report --formato csv|tabela`: relatório diretório x estado. Lotes de 500 `job_id` por consulta.
- `imgproc-admin scratch-amostra --jobs <id,id,...>`: copia metadados (nomes, tamanhos, datas, EXIF sem GPS) para `/scratch/quarentena/pm-amostra/`.
- `imgproc-admin scratch-limpar --lista <arquivo> --lote <n>`: remove diretórios listados; padrão de lote 100, máximo aceito 500.
- `imgproc-admin teste-ponta --amostra <caminho> --aguardar <s>`: envia imagem sintética e acompanha até `imagem.publicada`.
