# RB-274 — Estabilização da catalog-api

## Alerta relacionado

`OPS-4821` — taxa de erros HTTP 5xx acima de 12% por cinco minutos após uma implantação.

## Procedimento

1. Suspender novas implantações da `catalog-api` no ambiente afetado.
2. Registrar no incidente o identificador da revisão retornado por
   `kubectl -n catalog rollout history deployment/catalog-api`.
3. Reverter a implantação com `kubectl -n catalog rollout undo deployment/catalog-api`.
4. Acompanhar a estabilização com
   `kubectl -n catalog rollout status deployment/catalog-api --timeout=180s`.
5. Encerrar a contenção somente depois que a taxa de erros permanecer abaixo de 2% durante
   dez minutos.

## Restrição

Não reiniciar pods individualmente. Essa ação apaga a relação entre a falha e a revisão que
precisa ser registrada no incidente.
