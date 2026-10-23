# RB-381 - payments-worker: fila parada depois da rotação da credencial do broker

Revisão 1 do runbook. Responsável: time de pagamentos.

## Quando usar

Use este runbook quando a fila de cobrança para de ser consumida logo depois da rotação da credencial do broker. Os workers mantêm a conexão aberta com a credencial antiga e só leem a nova quando reiniciam.

## Reinício dos workers

1. Confirme no painel do broker que a credencial nova está ativa.
2. Reinicie todos os workers de uma vez:

```bash
kubectl -n pagamentos rollout restart deploy/payments-worker
```

3. Acompanhe até todos os pods ficarem prontos com `kubectl -n pagamentos rollout status deploy/payments-worker`.

## Verificação

A recuperação está confirmada quando a profundidade da fila cai de forma sustentada e o log dos workers não mostra mais `AUTH_FAILED`. Registre no ticket o horário da rotação e o horário do reinício.
