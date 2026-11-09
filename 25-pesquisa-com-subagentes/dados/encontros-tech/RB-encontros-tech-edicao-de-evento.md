---
projeto: encontros-tech
tipo: runbook
commit: 0f5bbad
---

# RB encontros-tech: organizador não consegue editar o evento

## Quando usar

Um organizador pede para alterar um evento já cadastrado e não tem mais o link de edição, ou o link devolve "não encontrado".

## Como a edição funciona

O encontros-tech não tem login. Cada evento recebe na criação um `edit_token`, um UUID único, e só quem tem o token edita o evento:

- página: `/events/edit/<token>`
- API: `GET` e `PUT` em `/api/events/by-token/<token>`. No commit `0f5bbad` essas rotas respondem 500 (mesmo erro de `model_dump` da API de listagem); use a página.

Depois do cadastro pelo formulário, a aplicação redireciona para `/?created=<id>&token=<token>`, e a página inicial mostra o link de edição uma única vez. A edição pelo `id` não existe.

## Diagnóstico

1. Link com "não encontrado": confira se o token foi copiado inteiro. A busca é por igualdade exata, e o log registra só os 8 primeiros caracteres: `Evento não encontrado para token: 3f2a9c1b...`.
2. Organizador sem link: não existe rota para recuperar ou reenviar o token.

## Procedimento para recuperar o token

O token só pode ser lido no banco. A consulta precisa de aprovação do responsável pelo projeto, porque o token dá acesso de edição:

```sql
SELECT id, title, edit_token FROM events WHERE id = <id do evento>;
```

Envie o link `/events/edit/<token>` só para o organizador que cadastrou o evento.

## Verificação

O link abre o formulário de edição com os dados do evento.
