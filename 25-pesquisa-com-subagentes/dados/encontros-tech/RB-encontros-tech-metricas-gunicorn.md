---
projeto: encontros-tech
tipo: runbook
commit: 0f5bbad
---

# RB encontros-tech: métricas inconsistentes com Gunicorn

## Quando usar

Com o encontros-tech rodando em Gunicorn com vários workers, os contadores do `/metrics` sobem e descem entre uma raspagem e outra, e o painel mostra taxas de requisição sem sentido.

## Causa provável

Cada worker do Gunicorn é um processo separado, com os próprios contadores em memória. Cada raspagem do Prometheus cai num worker diferente e lê só os números daquele worker.

O `main.py` cria o diretório `PROMETHEUS_MULTIPROC_DIR` (padrão `/tmp/prometheus_multiproc`) na subida. Mas criar o diretório não basta: a biblioteca `prometheus_client` só entra no modo multiprocesso quando a variável `PROMETHEUS_MULTIPROC_DIR` está no ambiente do processo antes de o Gunicorn subir. O valor padrão definido em `settings.py` não é exportado para o ambiente.

## Diagnóstico

1. Veja se a variável está no ambiente do Gunicorn:

```bash
echo "$PROMETHEUS_MULTIPROC_DIR"
```

2. Raspe o `/metrics` várias vezes seguidas e compare um contador:

```bash
for i in 1 2 3 4; do curl -s http://localhost:8000/metrics | grep '^flask_http_request_total' | head -1; done
```

Valores que sobem e descem confirmam a leitura por worker.

## Correção

Exporte `PROMETHEUS_MULTIPROC_DIR` antes de iniciar o Gunicorn, aponte para um diretório vazio e limpe esse diretório a cada reinício. Arquivos de uma execução anterior se misturam com os novos.

## Verificação

Raspagens seguidas mostram contadores que só crescem.
