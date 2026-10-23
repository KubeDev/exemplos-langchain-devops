# RB-905 - Volume temporário cheio no image-processor

**Tipo:** runbook
**Serviço:** image-processor
**Alerta:** MED-3304
**Equipe responsável:** mídia
**Ambiente:** laboratório fictício da aula

## Objetivo e limites

Este runbook orienta a estabilização do image-processor quando o volume temporário fica cheio e os trabalhos de processamento de imagens deixam de terminar. A intervenção protege arquivos de trabalhos em andamento e evidências do incidente. Não autoriza apagar diretórios inteiros, limpar arquivos de origem ou remover dados cujo dono não tenha sido identificado. Uma fila grande, sozinha, não é razão para limpar disco: o atraso pode resultar de CPU insuficiente, de uma dependência externa lenta ou de uma entrada incomum de imagens.

O serviço recebe imagens originais, cria versões derivadas e grava arquivos intermediários antes de publicar o resultado. O armazenamento temporário deveria ser liberado ao fim de cada trabalho. Se a limpeza falha, arquivos de tarefas já concluídas se acumulam até impedir novos trabalhos. A pressão no volume pode causar reinícios dos pods; esses reinícios escondem a causa se a equipe observar apenas o estado atual do processo.

## Sinais iniciais

O alerta MED-3304 indica uso elevado do volume temporário. Confirme a porcentagem ocupada, a velocidade de crescimento e o espaço livre real em cada pod. Compare o horário do alerta com aumento na taxa de entrada, implantação recente e mudanças na política de retenção. Verifique a fila de trabalhos, os reinícios e as mensagens de erro de escrita. Uma falha em armazenamento definitivo pode produzir erro de publicação mesmo com espaço temporário disponível; se esse for o caso, siga o procedimento da dependência.

Os arquivos temporários podem conter cópias de imagens ainda não publicadas. Trate nomes e caminhos como dados operacionais, mas não exponha imagens de clientes durante a investigação. Para a aula, todos os nomes e métricas são fictícios. Em um incidente real, a política de dados e os controles de acesso da equipe prevalecem sobre qualquer exemplo didático.

## Investigação ordenada

1. Anote a ocupação de cada volume, a taxa de crescimento, os reinícios e a idade do trabalho mais antigo na fila. Separe pods saudáveis dos que estão em ciclo de reinício.
2. Identifique quais diretórios são temporários e quais contêm arquivos de origem ou de saída. Consulte a documentação do serviço antes de selecionar qualquer caminho para limpeza.
3. Cruze identificadores de arquivos temporários com o estado dos trabalhos. Um arquivo associado a trabalho ativo ou de estado desconhecido não pode ser removido nesta etapa.
4. Compare a taxa de entrada e a duração média de processamento com o padrão anterior. Um pico legítimo pode exigir redução temporária da entrada ou aumento de capacidade, sem indicar vazamento.
5. Verifique se houve implantação ou alteração na rotina de limpeza antes do crescimento do disco. Observe logs de falha de remoção após conclusão de trabalhos.
6. Registre a hipótese, a lista de arquivos elegíveis e a aprovação do responsável. A lista precisa permitir auditoria posterior sem copiar dados sensíveis.

## Estabilização

Se o espaço estiver prestes a esgotar e o sistema de filas permitir, pause novas entradas para reduzir a pressão. Com aprovação, remova somente arquivos temporários identificados como pertencentes a trabalhos concluídos. Faça a remoção em lotes pequenos, conferindo o espaço liberado e o efeito sobre o serviço após cada lote. Preserve uma amostra de evidências que ajude a reproduzir a falha de limpeza. Não remova arquivos de trabalhos ativos, mesmo quando parecem antigos.

Retome o consumo gradualmente quando houver espaço suficiente para executar novos trabalhos. Monitore reinícios, taxa de conclusão, tempo de espera e velocidade de ocupação do volume. Se o espaço voltar a cair rapidamente, interrompa a retomada e investigue a rotina de retenção; repetir a limpeza indefinidamente esconde a falha e aumenta o risco de apagar dados necessários.

## Verificação e escalonamento

A recuperação exige espaço livre estável, ausência de novos reinícios relacionados a disco e fila diminuindo de forma sustentada. Confira uma imagem de teste do início ao fim do fluxo, sem usar material de cliente. Registre o volume liberado, a quantidade de trabalhos preservados, a aprovação e as pendências de correção definitiva.

Escalone para a equipe de mídia quando não for possível distinguir arquivos concluídos de ativos, quando a limpeza não liberar espaço ou quando a ocupação voltar a crescer no mesmo ritmo. Envie métricas, horários, versões implantadas e amostras sanitizadas. O post-mortem PM-041 descreve a falha anterior da rotina de limpeza, mas não serve como autorização para repetir a mesma remoção sem verificar o estado atual.
