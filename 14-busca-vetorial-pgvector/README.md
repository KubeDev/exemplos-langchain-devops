# 14 — Busca vetorial de documentos operacionais

Este exemplo indexa três runbooks em Markdown e três post-mortems em PDF no PostgreSQL com
pgvector. A indexação e a busca rodam em processos CLI distintos. A busca devolve o texto
recuperado, a origem e a distância de cosseno; nenhum resultado é enviado a um modelo de geração.
Os seis documentos são fictícios e não representam procedimentos de uma operação real.

## Preparação

Use Python 3.12, `uv`, Docker com Compose e uma chave da API da OpenAI. Nesta pasta:

```bash
cp .env.example .env
uv sync --locked
docker compose up -d --wait
```

Preencha `OPENAI_API_KEY` no `.env`. A porta local do banco é `55434`; o volume do Compose
preserva os dados depois que os processos Python terminam. A indexação chama a API de
embeddings da OpenAI e tem custo por tokens de entrada.

## Indexar

```bash
uv run indexar
```

O comando lê Markdown como texto UTF-8 e extrai o texto dos PDFs com `pypdf`. Depois mostra
quantas unidades foram lidas, gera os
embeddings com `text-embedding-3-small` em 1536 dimensões e os persiste. Cada execução
substitui a coleção inteira. Os PDFs têm uma página e texto selecionável; nenhum documento
é dividido em chunks nesta aula.

## Buscar

Em outro processo, depois que `indexar` terminar:

```bash
uv run buscar "O consumidor da fila parou depois da troca da credencial. Como estabilizar?" --k 3
uv run buscar "A API passou a falhar depois da nova versão. O que devo verificar?" --k 2
```

`--k` limita a quantidade de resultados e vale 3 quando omitido. Cada resultado mostra
origem, texto e **distância de cosseno**: menor distância significa vetor mais próximo,
não uma porcentagem de relevância nem prova de que o texto responde à pergunta.

O comando lê do banco o identificador e a dimensão do modelo usado na indexação. Se a
configuração de busca divergir, ele interrompe a consulta e orienta a reconstrução do
índice. O mesmo `text-embedding-3-small` converte os documentos e a pergunta.

## Arquivos

- `dados/`: três runbooks `.md` e três post-mortems `.pdf` fictícios;
- `src/busca_vetorial_pgvector/indexar.py`: extração, embedding LangChain e persistência;
- `src/busca_vetorial_pgvector/buscar.py`: compatibilidade, `k` e resultados;
- `compose.yaml`: PostgreSQL com pgvector e volume persistente.

O exemplo termina na recuperação. Estratégias de chunking, indexação incremental e uso
dos trechos pelo agente são assuntos das aulas seguintes.
