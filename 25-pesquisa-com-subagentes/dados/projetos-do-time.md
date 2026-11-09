---
projeto: geral
tipo: guia
commit: -
---

# Projetos do time

Documento de entrada para quem chega no time. Lista os projetos mantidos, onde está o código e qual documento ler primeiro.

## Quais projetos o time mantém

| Projeto | O que é | Stack | Repositório |
|---|---|---|---|
| kube-news | Portal de notícias com listagem, cadastro e visualização de notícias | Node.js, Express, EJS, Sequelize, PostgreSQL | https://github.com/KubeDev/kube-news |
| encontros-tech | Agenda de eventos de tecnologia, com cadastro e edição por token | Python, Flask, SQLAlchemy, PostgreSQL | https://github.com/KubeDev/encontros-tech |

Os dois projetos usam PostgreSQL, mas configuram a conexão de formas diferentes. Antes de seguir um procedimento de banco, confirme de qual projeto ele é.

## Por onde começar

1. Leia o guia do projeto (`GUIA-kube-news.md` ou `GUIA-encontros-tech.md`): como rodar, variáveis e rotas.
2. Leia a referência do projeto (`REF-kube-news.md` ou `REF-encontros-tech.md`): mapa de pastas e o commit que a documentação descreve.
3. Os runbooks (`RB-*`) dizem o que fazer diante de um sintoma.
4. Os post-mortems (`PM-*`) contam incidentes que já aconteceram em produção e o que mudou depois.

## Como os projetos rodam em produção

Cada projeto roda direto num servidor Linux, sem container: o kube-news com `npm start` dentro de `src/`, o encontros-tech com `gunicorn` dentro de `src/`. O banco é um PostgreSQL gerenciado, e o Prometheus raspa a rota `/metrics` de cada aplicação.

| Projeto | Servidor | Porta | Banco |
|---|---|---|---|
| kube-news | `kube-news-prod-01` | 8080 | `pg-prod.interno`, base `kubedevnews` |
| encontros-tech | `encontros-prod-01` | 8000 | `pg-prod.interno`, base `encontros_tech` |

## O que esta documentação não cobre

A documentação descreve o estado atual de cada repositório. Containerização, Kubernetes e pipeline de entrega não fazem parte do código hoje e não estão descritos aqui.
