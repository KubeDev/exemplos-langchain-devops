---
projeto: encontros-tech
tipo: runbook
commit: 0f5bbad
---

# RB encontros-tech: aplicação não conecta no banco

## Quando usar

O encontros-tech não sobe. O log para em `Criando tabelas no banco de dados` e mostra um erro do SQLAlchemy (`OperationalError`, conexão recusada ou falha de autenticação).

## Como o encontros-tech monta a conexão

A conexão inteira vem de uma variável só, a `DATABASE_URL`, lida em `src/core/settings.py`. Se ela não estiver no ambiente nem num `.env`, o código usa o padrão `postgresql://encontros_tech:encontros_tech@localhost:5432/encontros_tech`, que procura o banco na própria máquina.

A primeira coisa que a aplicação faz na subida é criar as tabelas (`create_all`). Por isso o erro de banco aparece antes de qualquer requisição.

## Diagnóstico

1. Veja se a variável chegou ao processo:

```bash
echo "$DATABASE_URL"
ls -la src/.env .env
```

2. Variável vazia e nenhum `.env` significam o padrão `localhost`. O `.env` é ignorado pelo git, então ele não chega ao servidor junto com o código.
3. Confira na URL o host, a base e o `sslmode`. Banco gerenciado que exige SSL precisa de `?sslmode=require` no fim da URL.
4. Teste a mesma URL direto:

```bash
psql "$DATABASE_URL"
```

## Correção

Defina a `DATABASE_URL` no ambiente do processo ou num `.env` em `src/`, e reinicie o Gunicorn.

## Verificação

O log mostra `Criando tabelas no banco de dados` seguido de `Aplicação Flask inicializada - Versão: <versão>`, e a página inicial lista os eventos.
