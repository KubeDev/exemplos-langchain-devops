# pedidos-worker

Worker que consome a fila de pedidos. Expõe `GET /healthz` na porta 8080.

Roda em container e é publicado no Kubernetes pelos manifestos em `k8s/`.
