---
projeto: kube-news
tipo: post-mortem
commit: aab9356
---

# PM kube-news: carga pela API derrubou a aplicação

## Resumo

Em 03/06/2026 uma carga de notícias pela rota `POST /api/post`, feita a partir de um feed de parceiro, derrubou o processo do kube-news em produção. Um dos artigos tinha título com mais de 255 caracteres. A API não valida tamanho, o banco recusou a gravação, e o erro não tratado encerrou o processo do Node.

## Impacto

- Duração: 18 minutos fora do ar (10:22 às 10:40)
- 34 notícias do lote foram gravadas antes do erro; as restantes não
- Três notícias gravadas tinham título acima de 30 caracteres e quebraram o layout da página inicial

## Linha do tempo

| Horário | Evento |
|---|---|
| 10:22 | Log de `kube-news-prod-01`: `Request Type: POST /api/post`, seguido do conteúdo de `artigos` |
| 10:22 | Terminal: `SequelizeDatabaseError: value too long for type character varying(255)` |
| 10:22 | O processo do Node encerra com rejeição de promessa não tratada |
| 10:31 | Plantonista encontra a mensagem do Sequelize no terminal |
| 10:38 | Processo reiniciado; o lote é dividido e revisado à mão |
| 10:40 | Aplicação de volta |

## Causa raiz

O formulário `POST /post` valida título com menos de 30 caracteres, resumo com menos de 50 e descrição com menos de 2000. A rota `POST /api/post` grava cada artigo direto, sem nenhuma dessas regras. No banco, título e resumo são texto de até 255 caracteres. O `await models.Post.create(...)` dentro da rota não tem tratamento de erro, e a rejeição não tratada encerra o processo.

## O que mudou depois

- Toda carga pela API passa antes por uma conferência dos limites do formulário
- O runbook `RB-kube-news-carga-de-noticias.md` registra os limites e o problema da porta no `popula-dados.http`
- O processo em produção passou a ser reiniciado automaticamente pelo gerenciador de serviços do servidor quando encerra
