---
projeto: kube-news
tipo: runbook
commit: aab9356
---

# RB kube-news: carga de notícias pela API

## Quando usar

Para popular o kube-news com várias notícias de uma vez, ou quando a carga com o arquivo `popula-dados.http` falha.

## A rota de carga

`POST /api/post` recebe um JSON com a lista `artigos`. Cada artigo tem `title`, `resumo` e `description`:

```json
{
  "artigos": [
    {"title": "Kubernetes na Nuvem", "resumo": "Gerencie contêineres na nuvem.", "description": "Texto da notícia."}
  ]
}
```

A rota grava cada artigo e devolve a própria lista. Ela não valida tamanho de campo.

## Problema conhecido: porta do popula-dados.http

O arquivo `popula-dados.http` aponta para `http://localhost:4503/api/post`, mas a aplicação escuta sempre na 8080. Usar o arquivo sem ajustar a porta dá conexão recusada.

## Procedimento

1. Ajuste a URL para a porta 8080, no arquivo ou no comando:

```bash
curl -X POST http://localhost:8080/api/post \
  -H "Content-Type: application/json" \
  -d @artigos.json
```

2. Mantenha os mesmos limites do formulário: título com menos de 30 caracteres, resumo com menos de 50 e descrição com menos de 2000. A API aceita mais, mas o banco recusa título ou resumo acima de 255 caracteres e descrição acima de 2000.

## Verificação

A página inicial lista as notícias novas, e o terminal mostra `Request Type: POST /api/post` seguido do conteúdo de `artigos`.
