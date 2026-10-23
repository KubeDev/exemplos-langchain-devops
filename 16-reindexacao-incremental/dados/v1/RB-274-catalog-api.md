# RB-274 - catalog-api: readiness falhando depois do deploy

Revisão 1 do runbook. Responsável: time de catálogo.

## Quando usar

Use este runbook quando, depois de um deploy da catalog-api, pods da revisão nova ficam fora do Service por falha de readiness e a taxa de erro da rota de ofertas sobe. Rollback não é o primeiro passo: confirme antes se a falha é da revisão nova.

## Diagnóstico

1. Compare as revisões em execução com `kubectl -n catalogo get rs -l app=catalog-api`.
2. Liste os eventos de readiness com `kubectl -n catalogo get events --field-selector involvedObject.kind=Pod`.
3. Teste um pod de cada revisão por port-forward, com a mesma rota e o mesmo SKU de teste:

```bash
kubectl -n catalogo port-forward pod/<pod> 18080:8080
curl -s http://localhost:18080/v1/products/SKU-TESTE-0001/offers
```

## Decisão

Se só a revisão nova falha, faça o rollback com `kubectl -n catalogo rollout undo deploy/catalog-api`. Se as duas revisões falham, o problema está numa dependência: siga para o runbook da dependência e não faça rollback.
