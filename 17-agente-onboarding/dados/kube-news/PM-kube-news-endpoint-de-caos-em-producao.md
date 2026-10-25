---
projeto: kube-news
tipo: post-mortem
commit: aab9356
---

# PM kube-news: rota de simulação de falha chamada em produção

## Resumo

Em 12/03/2026 o kube-news de produção passou 47 minutos devolvendo 500 em todas as páginas. Um teste de resiliência que deveria rodar contra a máquina de homologação foi disparado contra `kube-news-prod-01` e chamou `PUT /unhealth`. O monitoramento não alertou, porque o `/metrics` continuou respondendo.

## Impacto

- Duração: 47 minutos (14:05 às 14:52)
- Leitores receberam página em branco com status 500
- Nenhuma notícia foi perdida; só a leitura e o cadastro ficaram indisponíveis

## Linha do tempo

| Horário | Evento |
|---|---|
| 14:05 | Script de resiliência executado com a variável de destino apontando para produção |
| 14:05 | Log de `kube-news-prod-01`: `Request Type: PUT /unhealth` |
| 14:06 | Requisições à `/` passam a devolver 500 |
| 14:06 | A raspagem do Prometheus segue com sucesso; `up{job="kube-news"}` continua 1 |
| 14:38 | Primeira reclamação de leitor chega ao time |
| 14:45 | Plantonista confirma 500 no `/health` e 200 no `/metrics` |
| 14:51 | Processo reiniciado (`npm start` em `src/`) |
| 14:52 | `/health` devolve `{"state":"up","machine":"kube-news-prod-01"}` |

## Causa raiz

A rota `PUT /unhealth` muda o estado interno para não saudável, e o middleware de saúde passa a responder 500 a toda requisição. A aplicação não tem rota para voltar ao estado saudável: só o reinício resolve. A rota está exposta em qualquer ambiente, inclusive produção, e não exige autenticação.

## Por que demorou

O `express-prom-bundle` responde o `/metrics` antes do middleware de saúde. O Prometheus continuou raspando com sucesso, e o único alerta configurado era sobre a métrica `up`. Nenhum alerta olhava a taxa de respostas 500.

## O que mudou depois

- Alerta novo sobre a proporção de status 500 em `http_request_duration_seconds_count`
- Checagem sintética periódica do `/health`, de fora do servidor
- O script de resiliência passou a recusar destino com `prod` no nome
- O runbook `RB-kube-news-500-em-todas-as-rotas.md` foi escrito a partir deste incidente
