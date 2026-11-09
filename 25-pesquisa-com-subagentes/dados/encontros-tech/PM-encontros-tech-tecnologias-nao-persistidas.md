---
projeto: encontros-tech
tipo: post-mortem
commit: 0f5bbad
---

# PM encontros-tech: tecnologias dos eventos nunca foram gravadas

## Resumo

Entre 10/07 e 24/07/2026, organizadores relataram que as tecnologias preenchidas no formulário de cadastro (Python, Kubernetes e outras) não apareciam em lugar nenhum depois. Não era perda de dado em produção: o campo nunca foi gravado. O formulário e o esquema aceitam `technologies`, mas a tabela `events` não tem essa coluna.

## Impacto

- Nenhum evento cadastrado tem tecnologias guardadas
- Organizadores refizeram cadastros achando que tinham errado o preenchimento, o que gerou eventos duplicados
- Nenhuma indisponibilidade

## Linha do tempo

| Data | Evento |
|---|---|
| 10/07 | Organizador cadastra um evento pelo formulário com "Python, Kubernetes, Prometheus" no campo de tecnologias |
| 10/07 | Log: `INFO | encontros-tech.event_service | log_business_event:141 | BUSINESS | EVENT_CREATED | event_id=318 | ... | technologies_count=3` |
| 10/07 | A página do evento não mostra as tecnologias; o organizador cadastra o evento de novo |
| 22/07 | Terceira reclamação; o time abre a investigação |
| 24/07 | Consulta `SELECT * FROM events WHERE id = 318` mostra que não existe coluna de tecnologias |
| 24/07 | Leitura de `create_event`: o comentário diz "Por enquanto, não persistimos technologies no banco, apenas retornamos no objeto" |

## Causa raiz

O formulário `POST /events/` lê o campo `technologies`, separa por vírgula e monta o `EventCreate` com a lista. Em `src/services/event_service.py`, `create_event` grava só título, descrição, data e local; a lista é atribuída ao objeto depois do `commit`, só em memória. A edição faz o mesmo em `update_event`. O log `technologies_count=3` reforçou a impressão de que o dado tinha sido salvo.

## O que mudou depois

- O guia do projeto e a referência registram que `technologies` não é persistido
- Os eventos duplicados foram removidos com aprovação dos organizadores
- Pedido de mudança aberto no repositório para criar a coluna ou retirar o campo do formulário
