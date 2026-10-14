# RB-274 - Erros 5xx na catalog-api após implantação

**Tipo:** runbook
**Serviço:** catalog-api
**Alerta:** OPS-4821
**Equipe responsável:** plataforma
**Ambiente:** laboratório fictício da aula

## Objetivo e limites

Este runbook orienta a investigação de erros HTTP 5xx na catalog-api quando uma implantação recente pode ter alterado o comportamento do serviço. Ele não autoriza rollback automático. O operador precisa confirmar a relação entre a mudança e o sintoma, registrar evidências e obter a aprovação do responsável pelo incidente antes de reverter uma versão. O procedimento não cobre indisponibilidade do banco de catálogo, falha de rede entre serviços nem erro provocado por carga acima da capacidade planejada; esses cenários exigem diagnóstico próprio.

A catalog-api atende consultas de produto vindas da aplicação de loja. Ela depende de um banco de catálogo para leitura e de um serviço de preços para compor parte das respostas. Uma mesma resposta 5xx pode surgir de uma exceção introduzida no código, de configuração ausente, de uma dependência indisponível ou de esgotamento de recursos. Por isso, a hora de início dos erros é uma pista, não uma prova da causa.

## Sinais que ativam o procedimento

O alerta OPS-4821 dispara quando a taxa de respostas 5xx ultrapassa o limite operacional por alguns minutos. Compare a curva de erros com o início e o término da implantação. Verifique se a falha está concentrada nos pods da nova revisão ou se atinge igualmente as revisões antigas. Confira a prontidão dos pods, a quantidade de reinícios, a latência de consultas simples e os logs de aplicação com o identificador da revisão. Preserve pelo menos uma amostra de requisição falha, com dados sensíveis removidos.

Uma página de produto que falha por timeout no serviço de preços pode parecer a mesma regressão aos olhos do usuário. Se os erros começaram antes da implantação, se a revisão antiga apresenta a mesma falha ou se o banco não responde, interrompa a hipótese de rollback e procure a equipe responsável pela dependência. A ausência dessas verificações pode restaurar uma versão antiga sem resolver o incidente.

## Sequência de diagnóstico

1. Anote o identificador da versão implantada, o horário da mudança, a taxa de 5xx anterior e a taxa atual. Registre também o número de pods saudáveis por revisão.
2. Compare requisições de leitura simples com requisições que consultam preços. Se somente o segundo grupo falhar, investigue a dependência antes de atribuir a causa ao código da catalog-api.
3. Confira eventos de prontidão e reinício. Pods que nunca ficam prontos após a mudança apontam para inicialização ou configuração; pods prontos com exceções em uma rota apontam para falha de execução.
4. Consulte o histórico de mudanças do mesmo intervalo. Uma rotação de credencial, alteração de Secret ou mudança de rota pode coincidir com a implantação e produzir a mesma correlação temporal.
5. Peça à equipe de aplicação que compare a configuração exigida pela nova versão com a configuração presente no ambiente. Não copie valores secretos para o registro do incidente.
6. Formule a hipótese mais forte e anote qual evidência a sustenta e qual observação a refutaria. Esta anotação acompanha o pedido de aprovação.

## Decisão de estabilização

Considere a reversão quando os erros surgirem com a revisão nova, a revisão anterior tiver atendido as mesmas consultas normalmente e não houver sinal mais forte de falha em dependência. O responsável pelo incidente deve aprovar a ação e combinar uma janela de observação. Reverter é uma intervenção de produção, mesmo quando o comando é curto. Registre quem autorizou, qual versão era a anterior e como a equipe confirmará que a mudança produziu o efeito esperado.

Depois da aprovação, restaure a última revisão estável pelo processo operacional da equipe. Não improvise uma versão intermediária e não altere simultaneamente o banco ou o serviço de preços: mudanças paralelas dificultam a atribuição de causa. Acompanhe a taxa de 5xx, a prontidão, os reinícios e uma consulta de produto representativa por dez minutos. Se a taxa não cair, interrompa novas reversões e volte ao diagnóstico das dependências.

## Verificação e encerramento

O critério de sucesso exige três observações juntas: a taxa de 5xx retorna ao patamar anterior, os pods permanecem prontos e uma consulta representativa de catálogo funciona de ponta a ponta. Uma melhora de poucos segundos não encerra o incidente. Anote o horário da recuperação, a revisão ativa, a curva de erros após a ação e as pendências para correção definitiva. A correção do código ou da configuração defeituosa pertence ao trabalho posterior, não ao ato de estabilizar.

## Escalonamento e evidências

Escalone para a equipe de aplicação se a revisão antiga também falhar, se a reversão não reduzir os erros ou se uma dependência apresentar degradação. Inclua versão, horários, séries de erro e prontidão, amostras sanitizadas de logs e a hipótese descartada. Nunca inclua tokens, cabeçalhos de autenticação ou dados pessoais de clientes. O post-mortem PM-021 descreve um incidente anterior dessa família, mas o relato histórico não substitui estas verificações em um incidente novo.
