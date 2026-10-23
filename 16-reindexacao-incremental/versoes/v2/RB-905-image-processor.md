# RB-905 - image-processor: volume temporário cheio

Revisão 2 do runbook. Responsável: time de mídia.

## Quando usar

Use este runbook quando os pods do image-processor reiniciam por falta de espaço no volume temporário montado em `/tmp/imgproc`. O volume guarda os intermediários de cada imagem e deveria ser esvaziado ao fim de cada trabalho.

## Liberação de espaço

1. Confira o uso do volume com `kubectl -n midia exec <pod> -- df -h /tmp/imgproc`.
2. Não apague arquivos direto no pod: o `find -delete` já removeu intermediários de trabalhos em andamento. Use o comando de limpeza do próprio serviço, que só remove trabalhos encerrados:

```bash
kubectl -n midia exec <pod> -- imgproc-admin purge --older-than 2h
```

3. Repita em cada pod com uso acima de 80%.

## Verificação

A recuperação está confirmada quando o uso do volume fica abaixo de 50% e os pods param de reiniciar. Abra um ticket para o time de mídia investigar por que os intermediários não foram apagados.
