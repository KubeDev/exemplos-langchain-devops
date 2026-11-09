---
projeto: encontros-tech
tipo: referencia
commit: 0f5bbad
---

# Referência do encontros-tech

## Repositório

- URL: https://github.com/KubeDev/encontros-tech
- Branch: `main`
- Commit descrito por esta documentação: `0f5bbad` ("Removendo Docker")

Se o repositório estiver num commit mais novo, confira o código antes de seguir um procedimento daqui.

## Mapa de pastas

| Caminho | Conteúdo |
|---|---|
| `src/main.py` | cria a aplicação Flask, as tabelas, as métricas e registra as rotas |
| `src/core/settings.py` | variáveis de ambiente e valores padrão |
| `src/core/database.py` | engine do SQLAlchemy a partir da `DATABASE_URL` |
| `src/core/logging.py` | formato do log e os helpers `log_request`, `log_database_operation` e `log_business_event` |
| `src/models/event.py` | tabela `events` |
| `src/schemas/event.py` | esquemas Pydantic de entrada e saída |
| `src/services/event_service.py` | regras de criação, busca e edição |
| `src/routers/api_router.py` | rotas `/api/events` |
| `src/routers/page_router.py` | páginas HTML |
| `src/templates/` e `src/static/` | interface |
| `src/tests/` | testes com `pytest` |
| `api-requests.http` | requisições de exemplo para popular eventos na porta 8000 |

## Modelo de dados

A tabela `events` tem `id`, `title`, `description`, `date`, `location` e `edit_token`. O `edit_token` é um UUID gerado na criação, único por evento.

O formulário e o esquema aceitam também `technologies`, uma lista de tecnologias, mas esse campo não tem coluna na tabela e não é gravado.

## O que o repositório não tem

Não há Dockerfile, manifesto Kubernetes nem pipeline: o último commit removeu a configuração de Docker.
