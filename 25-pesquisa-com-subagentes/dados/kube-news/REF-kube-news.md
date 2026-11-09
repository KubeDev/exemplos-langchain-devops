---
projeto: kube-news
tipo: referencia
commit: aab9356
---

# Referência do kube-news

## Repositório

- URL: https://github.com/KubeDev/kube-news
- Branch: `main`
- Commit descrito por esta documentação: `aab9356` ("Melhorias na documentação.")

Se o repositório estiver num commit mais novo, confira o código antes de seguir um procedimento daqui.

## Mapa de pastas

| Caminho | Conteúdo |
|---|---|
| `src/server.js` | ponto de entrada: rotas de notícia, porta 8080 e métricas |
| `src/system-life.js` | rotas `/health`, `/ready`, `/unhealth`, `/unreadyfor/:seconds` e o middleware de saúde |
| `src/middleware.js` | contador `http_requests_total` e o log `Request Type` |
| `src/models/post.js` | conexão com o banco (variáveis `DB_*`) e o modelo `Post` |
| `src/views/` | templates EJS: `index`, `edit-news`, `view-news` e parciais |
| `src/static/` | CSS e imagens |
| `src/package.json` | dependências e o script `npm start` |
| `popula-dados.http` | requisição de exemplo para carregar notícias pela API |

## Modelo de dados

O único modelo é `Post`, na tabela gerada pelo Sequelize:

| Campo | Tipo no banco |
|---|---|
| `title` | texto de até 255 caracteres |
| `summary` | texto de até 255 caracteres |
| `content` | texto de até 2000 caracteres |
| `publishDate` | data |

Os limites menores (30 e 50) existem só no formulário, não no banco.

## O que o repositório não tem

Não há Dockerfile, manifesto Kubernetes, testes automatizados nem pipeline. O script `npm test` só imprime um erro.
