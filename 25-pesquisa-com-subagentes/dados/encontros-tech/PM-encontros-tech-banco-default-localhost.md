---
projeto: encontros-tech
tipo: post-mortem
commit: 0f5bbad
---

# PM encontros-tech: servidor novo subiu procurando o banco em localhost

## Resumo

Em 19/02/2026 o encontros-tech foi movido para o servidor novo `encontros-prod-01`. O código foi copiado do repositório, mas o `.env` não, porque ele é ignorado pelo git. Sem `DATABASE_URL`, a aplicação usou o valor padrão com `localhost` e não subiu.

## Impacto

- Duração: 38 minutos fora do ar (21:04 às 21:42)
- A migração estava anunciada, mas a volta prevista era em 10 minutos
- Nenhum dado perdido

## Linha do tempo

| Horário | Evento |
|---|---|
| 21:00 | Código copiado para `encontros-prod-01` a partir do `main` |
| 21:04 | Gunicorn iniciado em `src/` com 4 workers |
| 21:04 | Log: `2026-02-19 21:04:12,481 | INFO | encontros-tech | <module>:20 | Criando tabelas no banco de dados` |
| 21:04 | Erro: `sqlalchemy.exc.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused` |
| 21:04 | Os workers encerram na subida e o Gunicorn para |
| 21:20 | Time confere o PostgreSQL gerenciado: ativo e sem tentativas de conexão do servidor novo |
| 21:35 | `echo $DATABASE_URL` vazio e nenhum `.env` em `src/` |
| 21:40 | `.env` criado em `src/` com a `DATABASE_URL` de `pg-prod.interno` |
| 21:42 | Log: `Aplicação Flask inicializada - Versão: 1.0.0`; página inicial lista os eventos |

## Causa raiz

`src/core/settings.py` define um valor padrão para a `DATABASE_URL` apontando para `localhost`. Quando a variável não existe, a aplicação não falha por falta de configuração: ela tenta o banco local e falha com conexão recusada. A mensagem leva a investigar o banco, não a configuração.

## Por que demorou

O erro citava `localhost`, mas a leitura inicial foi de problema de rede entre o servidor novo e o banco. Só depois de ver que o banco não recebia tentativa nenhuma o time olhou o ambiente do processo.

## O que mudou depois

- A lista de migração de servidor ganhou o passo "criar o `.env` a partir do `.env.exemple`"
- O runbook `RB-encontros-tech-conexao-banco.md` explica o valor padrão e o primeiro comando de diagnóstico
- A subida passou a ser conferida pela linha `Aplicação Flask inicializada` no log, e não só pelo processo rodando
