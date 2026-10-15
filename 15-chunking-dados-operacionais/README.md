# 15 — Chunking de documentos operacionais

Este exemplo compara três estratégias de divisão de texto num runbook, depois divide a
documentação de três serviços fictícios com a estratégia de cada tipo de documento, gera os
embeddings, grava no PostgreSQL com pgvector e busca por similaridade. Nenhum resultado é enviado a
um modelo de geração.

Todos os dados são fictícios e não representam uma operação real.

## Preparação

Use Python 3.12, `uv`, Docker com Compose e uma chave da API da OpenAI. Nesta pasta:

```bash
cp .env.example .env
uv sync --locked
docker compose up -d --wait
```

Preencha `OPENAI_API_KEY` no `.env`. A porta local do banco é `55435`. A indexação chama a API
de embeddings da OpenAI e tem custo por tokens de entrada; `gerar-chunks` não precisa de chave nem
de banco.

## A base

| Dado | Arquivos | Natureza |
|---|---|---|
| Runbook, arquitetura, referência | `dados/RB-*.md`, `dados/ARQ-*.md`, `dados/REF-*.md` | texto com títulos Markdown |
| Post-mortem | `dados/PM-*.pdf` | texto extraído de PDF, sem títulos |

Log não entra na base: é consultado no sistema de logs por serviço, nível e horário, por uma
ferramenta do agente, e não recuperado por similaridade.

## As estratégias

As três seguem as famílias da [página de text splitters do LangChain](https://docs.langchain.com/oss/python/integrations/splitters).
Cada uma resolve o defeito da anterior.

| Estratégia | Função | Splitter | Sobreposição |
|---|---|---|---|
| Tamanho fixo | `dividir_por_tamanho_fixo()` | `CharacterTextSplitter(separator="")` | repete os últimos caracteres do chunk anterior |
| Recursivo | `dividir_recursivo()` | `RecursiveCharacterTextSplitter` | em geral repete unidades inteiras do fim do chunk anterior, às vezes nada |
| Seção | `dividir_por_secao()` | `MarkdownHeaderTextSplitter` | não usa |

O limite do modelo de embedding é contado em tokens; os mesmos splitters podem medir o tamanho em
tokens em vez de caracteres.

## Ver os chunks sem gerar embedding

```bash
uv run gerar-chunks
```

Divide o RB-381 com as três estratégias, na ordem, com tamanho 1000 e sobreposição 200, e imprime
uma linha por estratégia: quantos chunks saíram, o menor, o maior, o total de caracteres e quantos
caracteres foram repetidos pela sobreposição. No tamanho fixo, o menor chunk é o resto do fim do
documento; no recursivo, um trecho curto, e na seção, a menor seção. Os repetidos medem o custo da
sobreposição, não a qualidade do corte. Os parâmetros são constantes no topo de `gerar_chunks.py`.

## Indexar e buscar

```bash
uv run indexar
uv run buscar "A fila de cobrança parou depois da rotação da credencial do broker. Como reiniciar os workers do payments-worker com segurança?" --k 3
```

`indexar` usa `dividir_base()`: seção nos documentos Markdown e recursivo nos post-mortems em PDF
(1000 com sobreposição de 200, ponto de partida). Mostra os chunks por tipo com o maior de cada um e
os caracteres enviados ao modelo de embedding, e reconstrói a coleção `chunks` a cada execução. O
maior chunk é a medição: a seção não tem limite de tamanho porque a maior delas fica muito abaixo do
limite do modelo. `buscar` imprime os `k` chunks mais próximos com origem e distância.

## Um arquivo, uma leitura

Cada comando é um arquivo que se lê sozinho, de cima a baixo, sem importar nada de outro arquivo
do projeto. Por isso o recursivo e a seção aparecem duas vezes: em `gerar_chunks.py`, para a demo,
e em `indexar.py`, para a base inteira. A repetição é de propósito. Ao mudar uma dessas estratégias,
mude nos dois lugares.
