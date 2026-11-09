---
projeto: kube-news
tipo: runbook
commit: aab9356
---

# RB kube-news: 500 em todas as rotas

## Quando usar

Toda requisição ao kube-news devolve status 500 com corpo vazio: a página inicial, as notícias e o `/health`. O processo continua de pé e a porta 8080 continua aberta.

A exceção é o `/metrics`, que continua respondendo 200: o `express-prom-bundle` atende essa rota antes do middleware de saúde. Por isso a raspagem do Prometheus segue normal e a métrica `up` não acusa o problema.

## Causa provável

Alguém chamou `PUT /unhealth`. Essa rota existe para simular falha: ela muda a variável `isHealth` para `false`, e a partir daí o middleware `healthMid` responde 500 para qualquer requisição.

Não existe rota que devolva a aplicação ao estado saudável. O estado só volta ao normal quando o processo reinicia.

## Diagnóstico

1. Confirme que o processo está rodando e a porta responde:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/health
```

2. Status 500 também no `/health` indica o `/unhealth`. Se só o `/ready` falha, use o runbook `RB-kube-news-ready-500.md`.
3. Procure no terminal da aplicação a linha `Request Type: PUT /unhealth`.

## Correção

Reinicie o processo do kube-news. No servidor, pare o `npm start` em execução e suba de novo dentro de `src/`.

## Verificação

`/health` devolve 200 com `{"state":"up","machine":"<host>"}` e a página inicial lista as notícias.
