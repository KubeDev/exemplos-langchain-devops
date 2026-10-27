---
projeto: kube-news
tipo: runbook
commit: aab9356
---

# RB kube-news: /ready devolvendo 500

## Quando usar

O `/ready` do kube-news devolve 500, mas o `/health` e as páginas continuam respondendo 200.

## Causa provável

Alguém chamou `PUT /unreadyfor/:seconds`. A rota guarda um horário no futuro (agora mais N segundos), e enquanto esse horário não chega o `/ready` devolve 500. O resto da aplicação não é afetado.

## Diagnóstico

1. Compare as duas rotas:

```bash
curl -s -o /dev/null -w "ready %{http_code}\n" http://localhost:8080/ready
curl -s -o /dev/null -w "health %{http_code}\n" http://localhost:8080/health
```

2. `ready 500` com `health 200` confirma a indisponibilidade simulada.
3. Procure no terminal a linha `Request Type: PUT /unreadyfor/<segundos>` para saber por quanto tempo.

## Correção

Espere o prazo terminar: o `/ready` volta a 200 sozinho. Se o valor de segundos foi alto demais, reiniciar o processo também zera o prazo.

## Diferença para o 500 em todas as rotas

Se o `/health` também devolve 500, o problema não é este. Use `RB-kube-news-500-em-todas-as-rotas.md`.
