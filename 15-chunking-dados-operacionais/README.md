# 15 — Chunking de dados operacionais

Este exemplo divide documentação, logs e tickets de três serviços fictícios em chunks, indexa
duas configurações de chunk no PostgreSQL com pgvector e compara as duas com um conjunto de
perguntas de fragmento esperado. Nenhum resultado é enviado a um modelo de geração.

Todos os dados são fictícios e não representam uma operação real.

## Preparação

Use Python 3.12, `uv`, Docker com Compose e uma chave da API da OpenAI. Nesta pasta:

```bash
cp .env.example .env
uv sync --locked
docker compose up -d --wait
```

Preencha `OPENAI_API_KEY` no `.env`. A porta local do banco é `55435`. A indexação chama a API
de embeddings da OpenAI e tem custo por tokens de entrada.

## A base

| Dado | Arquivos | Natureza |
|---|---|---|
| Runbook, arquitetura, referência | `dados/RB-*.md`, `dados/ARQ-*.md`, `dados/REF-*.md` | texto com títulos Markdown |
| Post-mortem | `dados/PM-*.pdf` | texto extraído de PDF, sem estrutura |
| Log de aplicação | `dados/logs/*.jsonl` | um evento JSON por linha |
| Ticket | `dados/tickets.json` | registro com campos e histórico de comentários |

## Ver os chunks sem gerar embedding

```bash
uv run chunks dados/RB-381-payments-worker.md --estrategia inteiro
uv run chunks dados/RB-381-payments-worker.md --estrategia tamanho --tamanho 1000 --contendo "aprovação explícita"
uv run chunks dados/RB-381-payments-worker.md --estrategia secao --tamanho 3500 --contendo "aprovação explícita"
uv run chunks dados/logs/payments-worker.jsonl --estrategia janela --segundos 15 --contendo "14:04:1"
uv run chunks dados/logs/payments-worker.jsonl --estrategia janela --segundos 15 --sobreposicao 5 --contendo "14:04:1"
uv run chunks dados/tickets.json --estrategia ticket --tamanho 1500
```

O comando imprime cada chunk com tamanho, posição, seção ou janela, e termina com a quantidade
de chunks e o tamanho mínimo, mediano e máximo. `--contendo` filtra os chunks exibidos; o
resumo continua considerando todos.

| Estratégia | Função em `dividir.py` | Para quê |
|---|---|---|
| `inteiro` | nenhuma | o arquivo como uma unidade, como na Aula 06 |
| `tamanho` | `dividir_por_tamanho()` | recursivo por separador até caber no tamanho |
| `secao` | `dividir_por_secao()` | corta nos títulos; título, serviço e tipo vão no texto do chunk |
| `janela` | `janelas_de_log()` | eventos WARN e ERROR de um serviço em janelas de tempo |
| `ticket` | `dividir_tickets()` | um ticket por chunk; campos no metadado |

## Indexar as duas configurações

```bash
uv run indexar --config a
uv run indexar --config b
```

`configuracao_a()` trata tudo como texto: recursivo com 1000 caracteres e sobreposição de 150,
inclusive para o JSON dos logs e dos tickets. `configuracao_b()` escolhe a estratégia pela
natureza do dado; o tamanho de 3500 nos documentos saiu da medição das seções da base. Cada
configuração tem sua coleção (`chunks_a`, `chunks_b`) e cada execução reconstrói a coleção.

## Buscar e avaliar

```bash
uv run buscar "Como reiniciar os workers do payments-worker com segurança?" --config b --k 3
uv run avaliar
```

`perguntas.json` traz as perguntas, o tipo de dado e os fragmentos que precisam aparecer juntos
num mesmo chunk. `avaliar` mede duas coisas para cada configuração: se a resposta existe inteira
em algum chunk do índice (efeito do chunking) e se esse chunk volta entre os 4 mais próximos da
pergunta (efeito da busca). Também soma os caracteres recuperados, que é o texto que iria para o
contexto de um agente.
