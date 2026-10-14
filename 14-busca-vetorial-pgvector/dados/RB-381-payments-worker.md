# RB-381 - Fila parada no payments-worker após rotação de credencial

**Tipo:** runbook
**Serviço:** payments-worker
**Cenário:** falhas de autenticação e aumento da fila após rotação de credencial
**Responsável:** equipe de pagamentos (exemplo fictício)

## Quando usar

Use este procedimento quando o payments-worker deixar de consumir mensagens depois da rotação da credencial do broker e o alerta PAY-7712 disparar.

## Verificações

1. Compare o início da fila com o horário da rotação.
2. Confira erros de autenticação no worker sem exibir o valor do segredo nos logs.
3. Compare a versão do Secret referenciado pelo deployment com a versão aprovada no gerenciador de segredos.

## Estabilização

Se o Secret estiver desatualizado, corrija a referência pela rotina aprovada. Reinicie os workers de forma controlada para que carreguem a credencial vigente. Não cole credenciais em tickets, comandos ou logs. Monitore a taxa de consumo e a fila até o atraso cair.

## Critério de sucesso

As falhas de autenticação cessam e o atraso da fila diminui de forma sustentada. Se a autenticação continuar falhando, interrompa novas tentativas e escale para o responsável pelo broker.
