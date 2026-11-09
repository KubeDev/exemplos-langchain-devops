---
projeto: encontros-tech
tipo: post-mortem
commit: 0f5bbad
---

# PM encontros-tech: token de edição exposto nos logs

## Resumo

Em 07/05/2026 um evento publicado no encontros-tech teve título, data e local alterados por alguém que não era o organizador. O token de edição do evento estava gravado por inteiro no log da aplicação, e o log de produção era lido por uma ferramenta de busca de logs com acesso amplo.

## Impacto

- Um evento alterado indevidamente; a data errada ficou publicada por cerca de 6 horas
- Todos os tokens de eventos criados até a correção estavam nos logs retidos
- Nenhum outro dado sensível: o encontros-tech não guarda dado pessoal de participante

## Linha do tempo

| Horário | Evento |
|---|---|
| 06/05 18:30 | Evento criado pelo formulário; log: `INFO | encontros-tech.event_service | create_event:38 | Evento criado com sucesso: ID=212, Token=<token completo>` |
| 07/05 08:02 | Log: `INFO | encontros-tech.event_service | update_event:112 | Atualizando evento com token: 9b1e44c2...` |
| 07/05 14:10 | Organizador avisa que a data do evento mudou sem ele pedir |
| 07/05 14:40 | Time encontra o token completo no log de criação |
| 07/05 15:05 | Data do evento restaurada pelo organizador com o mesmo token |
| 07/05 16:30 | Acesso à ferramenta de busca de logs restrito ao time |

## Causa raiz

Em `src/services/event_service.py`, a função `create_event` registra em nível INFO a mensagem `Evento criado com sucesso: ID=..., Token=...` com o token inteiro. O resto da aplicação registra só os 8 primeiros caracteres. O token também aparece na URL do redirecionamento depois do cadastro (`/?created=<id>&token=<token>`). Como o token é a única proteção da edição, quem lê o log consegue editar qualquer evento.

## O que mudou depois

- Retenção dos logs antigos reduzida e acesso restrito ao time
- Pedido de mudança aberto no repositório para registrar só o prefixo do token, como no restante do código
- O runbook `RB-encontros-tech-edicao-de-evento.md` exige aprovação para ler um token no banco
