# RB-381 - Fila parada no payments-worker após rotação de credencial

**Tipo:** runbook
**Serviço:** payments-worker
**Alerta:** PAY-7712
**Equipe responsável:** pagamentos
**Ambiente:** laboratório fictício da aula

## Objetivo e limites

Este procedimento trata da perda de consumo da fila de pagamentos após a rotação da credencial usada pelo worker para se autenticar no broker. Seu objetivo é restabelecer o consumo sem expor segredos e sem processar mensagens duas vezes por uma intervenção precipitada. A simples presença de uma fila acumulada não prova falha de autenticação: lentidão no processamento, indisponibilidade do broker e aumento legítimo da taxa de entrada produzem sintomas parecidos.

O payments-worker recebe mensagens de cobrança, confirma seu processamento e publica um resultado para a aplicação de pedidos. A fila funciona como amortecedor entre a entrada de solicitações e o processamento. Quando os workers param, o atraso cresce mesmo que a aplicação de pedidos continue aceitando novas solicitações. O tempo de espera do cliente pode aumentar antes de surgir um erro direto na API. A equipe deve considerar esse impacto ao comunicar o incidente.

## Condições para usar este runbook

Use o runbook quando o alerta PAY-7712 indicar crescimento sustentado do atraso e os logs dos workers mostrarem falha de autenticação próxima ao horário de rotação da credencial. Registre o início da rotação, a versão de Secret esperada, a versão referenciada pelo deployment e a hora em que cada worker iniciou. Não registre o valor da credencial em tickets, terminal compartilhado ou captura de tela da aula.

Se os workers estão autenticados e processando lentamente, siga a investigação de desempenho. Se o broker inteiro está indisponível, escale para a equipe que o opera. Se uma mensagem específica provoca repetidos erros de negócio, isole essa mensagem pelo procedimento de fila de quarentena; reiniciar workers sem entender o erro apenas repete a falha.

## Diagnóstico em ordem

1. Compare a curva de mensagens pendentes, a taxa de entrada e a taxa de confirmação. Uma fila que cresce porque a entrada duplicou exige resposta diferente de uma fila com consumo zero.
2. Observe erros de autenticação nos logs sem imprimir cabeçalhos, senhas ou tokens. Conte quantos workers apresentam o erro e confira se ele começou após a rotação.
3. Consulte o identificador e a versão do Secret aprovado no gerenciador de segredos. Compare apenas identificadores e datas com a referência que o deployment usa.
4. Verifique quando os processos foram iniciados. Alguns workers leem credenciais somente na inicialização; nesses casos, corrigir um Secret não atualiza o valor já carregado na memória do processo.
5. Confirme com o responsável pelo broker se a credencial antiga foi revogada e se a nova já está ativa. Uma diferença de horário entre publicação e revogação pode explicar falhas intermitentes.
6. Registre a hipótese, a evidência a favor e um sinal que a refutaria. Peça aprovação antes de reiniciar componentes que processam pagamentos.

## Estabilização controlada

Se a referência ao Secret estiver errada, corrija-a pelo processo aprovado. Se a referência estiver correta, mas os workers ainda carregarem a versão antiga, faça um reinício controlado para que os novos processos obtenham a credencial vigente. Reinicie em lotes pequenos e acompanhe as confirmações de mensagens; desligar todos os workers ao mesmo tempo amplia o atraso e elimina capacidade de recuperação. Não altere o formato de mensagem nem limpe a fila durante a rotação.

Depois de cada lote, verifique se as novas instâncias se autenticam, consomem mensagens e confirmam o processamento. Observe também a fila de quarentena e os identificadores de transação para detectar repetição indevida. A queda do atraso deve ser sustentada, não um efeito temporário de uma única instância. Se a autenticação continuar falhando, pare novas tentativas, preserve os logs sanitizados e peça verificação da credencial e da política de acesso pelo responsável pelo broker.

## Critérios de recuperação

Considere o serviço estabilizado quando erros de autenticação cessarem, a taxa de confirmação superar a taxa de entrada por tempo suficiente para reduzir o atraso e não houver crescimento anormal da fila de quarentena. Confirme com a aplicação de pedidos que novas solicitações recebem resultado dentro do intervalo esperado. Registre a versão do Secret em uso e o horário de normalização; não registre o segredo.

## Escalonamento e aprendizado

Escalone quando a credencial aprovada não for aceita, quando o broker reportar falha geral ou quando o processamento voltar com risco de duplicação. Leve gráficos de entrada, confirmação e atraso, versões de Secret, horários de inicialização e amostras sanitizadas dos erros. O post-mortem PM-034 descreve um caso em que o Secret correto já estava disponível, mas os processos antigos continuaram com a credencial anterior. Ele ajuda a formular hipóteses; este runbook determina as verificações necessárias agora.
