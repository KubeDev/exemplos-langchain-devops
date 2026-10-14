# RB-905 - Volume temporário cheio no image-processor

**Tipo:** runbook
**Serviço:** image-processor
**Cenário:** falhas de processamento e reinícios por falta de espaço temporário
**Responsável:** equipe de mídia (exemplo fictício)

## Quando usar

Use este procedimento quando o image-processor acumular trabalhos e o alerta MED-3304 indicar pressão no volume temporário.

## Verificações

1. Confirme o uso do volume temporário e a taxa de reinícios dos pods.
2. Identifique se arquivos de trabalho concluído permaneceram no volume.
3. Compare o volume de entrada com a capacidade configurada antes de atribuir a causa a vazamento.

## Estabilização

Pause novas entradas se a fila permitir. Com aprovação do responsável, remova somente arquivos temporários identificados como concluídos; preserve arquivos de trabalhos ativos e evidências do incidente. Retome gradualmente o consumo e acompanhe espaço livre, reinícios e atraso da fila.

## Critério de sucesso

O espaço livre permanece estável, os pods deixam de reiniciar e a fila volta a diminuir. Se o volume encher novamente, escale para investigação da retenção de arquivos.
