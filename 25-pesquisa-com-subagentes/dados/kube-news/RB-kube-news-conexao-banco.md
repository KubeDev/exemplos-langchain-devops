---
projeto: kube-news
tipo: runbook
commit: aab9356
---

# RB kube-news: aplicação não conecta no banco

## Quando usar

O kube-news não sobe ou encerra logo depois de subir, com erro do Sequelize no terminal (`SequelizeConnectionError`, `SequelizeConnectionRefusedError` ou falha de autenticação).

## Como o kube-news monta a conexão

A conexão vem de seis variáveis separadas, lidas em `src/models/post.js`: `DB_HOST`, `DB_PORT`, `DB_DATABASE`, `DB_USERNAME`, `DB_PASSWORD` e `DB_SSL_REQUIRE`. Toda variável ausente cai num valor padrão: sem `DB_HOST`, a aplicação tenta `localhost`.

## Diagnóstico

1. Liste as variáveis que o processo recebeu:

```bash
env | grep '^DB_'
```

2. Variável ausente significa valor padrão. Sem `DB_HOST` no servidor de produção, a aplicação procura o banco na própria máquina.
3. Banco que exige SSL rejeita a conexão se `DB_SSL_REQUIRE` não for exatamente `true`. Os valores `True`, `1` e `yes` são tratados como falso pela função `strToBool`.
4. Teste o acesso ao banco a partir do servidor com as mesmas credenciais:

```bash
psql "host=$DB_HOST port=$DB_PORT dbname=$DB_DATABASE user=$DB_USERNAME sslmode=require"
```

## Correção

Corrija as variáveis no ambiente do processo e reinicie o `npm start`. Para banco gerenciado, use `DB_SSL_REQUIRE=true` em minúsculas.

## Verificação

A aplicação sobe, a página inicial lista as notícias e o terminal mostra `Request Type: GET /` sem erro do Sequelize.
