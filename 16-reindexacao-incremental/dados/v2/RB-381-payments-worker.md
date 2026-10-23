# RB-381 - payments-worker: fila parada depois da rotação da credencial do broker

Revisão 2 do runbook. Responsável: time de pagamentos.

## Quando usar

Use este runbook quando a fila de cobrança para de ser consumida logo depois da rotação da credencial do broker. Os workers mantêm a conexão aberta com a credencial antiga e só leem a nova quando reiniciam.

## Reinício dos workers

Não reinicie todos os workers de uma vez: o reinício em massa já duplicou cobranças, porque mensagens em processamento voltaram para a fila.

1. Confirme no painel do broker que a credencial nova está ativa.
2. Peça a aprovação do líder de plantão e do time de pagamentos e registre as duas no ticket.
3. Reinicie em lotes de 2 pods, esperando cada lote ficar pronto:

```bash
kubectl -n pagamentos delete pod <pod-1> <pod-2>
kubectl -n pagamentos rollout status deploy/payments-worker
```

## Verificação

A recuperação está confirmada quando a profundidade da fila cai de forma sustentada e o log dos workers não mostra mais `AUTH_FAILED`. Confira no relatório de conciliação que nenhuma cobrança foi duplicada no intervalo do reinício.
