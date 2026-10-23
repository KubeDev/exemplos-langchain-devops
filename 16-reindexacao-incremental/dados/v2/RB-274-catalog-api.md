# RB-274 - catalog-api: readiness falhando depois do deploy

Revisão 2 do runbook. Responsável: time de catálogo.

## Quando usar

Use este runbook quando, depois de um deploy da catalog-api, pods da revisão nova ficam fora do Service por falha de readiness e a taxa de erro da rota de ofertas sobe. Rollback não é o primeiro passo: confirme antes se a falha é da revisão nova.

## Diagnóstico

1. Compare as revisões em execução com `kubectl -n catalogo get rs -l app=catalog-api`.
2. Liste os eventos de readiness com `kubectl -n catalogo get events --field-selector involvedObject.kind=Pod`.
3. Teste um pod de cada revisão pelo Service de diagnóstico `catalog-api-debug`, com a mesma rota e o mesmo SKU de teste. Não use port-forward: ele foi bloqueado no cluster de produção.

```bash
kubectl -n catalogo run teste-oferta --rm -i --image=curlimages/curl --restart=Never -- \
  curl -s -H "X-Revisao: <hash-da-revisao>" http://catalog-api-debug/v1/products/SKU-TESTE-0001/offers
```

## Decisão

Se só a revisão nova falha, faça o rollback com `kubectl -n catalogo rollout undo deploy/catalog-api`. Se as duas revisões falham, o problema está numa dependência: siga para o runbook da dependência e não faça rollback.
