# RB-274 - Erros 5xx na catalog-api após implantação

**Tipo:** runbook
**Serviço:** catalog-api
**Cenário:** aumento de erros HTTP 5xx logo após uma nova versão
**Responsável:** equipe de plataforma (exemplo fictício)

## Quando usar

Use este procedimento quando a taxa de respostas 5xx da catalog-api subir após uma implantação e o alerta OPS-4821 disparar. Não presuma que toda falha 5xx exige rollback.

## Verificações

1. Compare o início dos erros com o horário da implantação.
2. Confira se os pods novos falham nas verificações de prontidão e se os pods antigos atendiam normalmente.
3. Verifique se houve mudança simultânea em dependências ou configuração.

## Estabilização

Se a nova versão for a causa provável, registre as evidências e solicite aprovação do responsável pelo incidente. Depois da aprovação, reverta a implantação para a última versão estável. Monitore a taxa de 5xx e a prontidão dos pods por dez minutos.

## Critério de sucesso

A taxa de 5xx volta ao patamar anterior, os pods ficam prontos e o catálogo responde a uma consulta de teste. Se os erros persistirem após a reversão, escale para a equipe de aplicação.
