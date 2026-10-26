# 15 — Chunking de documentos operacionais

Este exemplo compara duas estratégias de divisão de texto num runbook, depois divide a
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
de banco. O Compose também sobe o pgweb em <http://localhost:58435>, já conectado ao banco, para
ver os chunks gravados.

## A base

| Dado | Arquivos | Natureza |
|---|---|---|
| Runbook, arquitetura, referência | `dados/RB-*.md`, `dados/ARQ-*.md`, `dados/REF-*.md` | texto com títulos Markdown |
| Post-mortem | `dados/PM-*.pdf` | texto extraído de PDF, sem títulos |

Log não entra na base: é consultado no sistema de logs por serviço, nível e horário, por uma
ferramenta do agente, e não recuperado por similaridade.

## As estratégias

As duas seguem as famílias da [página de text splitters do LangChain](https://docs.langchain.com/oss/python/integrations/splitters).
O recursivo é o splitter que a documentação recomenda para texto genérico; a seção resolve o que ele
não resolve, o título longe do procedimento.

| Estratégia | Função | Splitter | Sobreposição |
|---|---|---|---|
| Recursivo | `dividir_recursivo()` | `RecursiveCharacterTextSplitter` | em geral repete unidades inteiras do fim do chunk anterior, às vezes nada |
| Seção | `dividir_por_secao()` | `MarkdownHeaderTextSplitter` | não usa |

O recursivo tem dois pontos de partida, escolhidos pelo tamanho da resposta, com sobreposição de 20%:

| Ponto de partida | Quando | Exemplo |
|---|---|---|
| 1000 caracteres, 200 de sobreposição | a resposta é um fato curto: um valor, uma configuração | referência, ticket |
| 2000 caracteres, 400 de sobreposição | a resposta é um trecho longo: um procedimento, uma linha do tempo | runbook, post-mortem |

São pontos de partida, não medição: a busca na própria base confirma ou corrige.

O limite do modelo de embedding é contado em tokens; os mesmos splitters podem medir o tamanho em
tokens em vez de caracteres.

## Ver os chunks sem gerar embedding

```bash
uv run gerar-chunks
```

Divide o RB-381 com o recursivo nos dois pontos de partida e depois por seção, e imprime uma linha
por divisão: quantos chunks saíram, o menor, o maior, o total de caracteres e quantos caracteres
foram repetidos pela sobreposição. No recursivo, o menor chunk é um trecho curto; na seção, a menor
seção. Os repetidos medem o custo da
sobreposição, não a qualidade do corte. Os parâmetros são constantes no topo de `gerar_chunks.py`.

## Indexar e buscar

```bash
uv run indexar
uv run buscar "A fila de cobrança parou depois da rotação da credencial do broker. Como reiniciar os workers do payments-worker com segurança?" --k 3
```

`indexar` usa `dividir_base()`: seção nos documentos Markdown e recursivo nos post-mortems em PDF
(2000 com sobreposição de 400, o ponto de partida de resposta longa). Mostra os chunks por tipo com o maior de cada um e
os caracteres enviados ao modelo de embedding, e reconstrói a coleção `chunks` a cada execução. O
maior chunk é a medição: a seção não tem limite de tamanho porque a maior delas fica muito abaixo do
limite do modelo. `buscar` imprime os `k` chunks mais próximos com origem e distância.

## Ver o que foi gravado

Abra <http://localhost:58435>. A tabela `langchain_pg_embedding` tem uma linha por chunk, com
texto, metadados e vetor. Na aba *Query*:

```sql
SELECT cmetadata->>'source'       AS origem,
       cmetadata->>'tipo'         AS tipo,
       cmetadata->>'secao'        AS secao,
       length(document)           AS caracteres,
       vector_dims(embedding)     AS dimensoes
FROM langchain_pg_embedding
ORDER BY origem, caracteres DESC;
```

Os chunks de Markdown trazem a `secao`; os de PDF, do recursivo, ficam sem ela. A coluna
`caracteres` é a mesma medição que o `indexar` imprime.

## Um arquivo, uma leitura

Cada comando é um arquivo que se lê de cima a baixo. O recursivo e a seção ficam em
`gerar_chunks.py`, onde a demo os mostra no RB-381; o `indexar.py` importa essas mesmas funções e
as aplica na base inteira. Assim a indexação usa exatamente as estratégias que a demo mediu, e
mudar uma estratégia é mudar um lugar só. As constantes de embedding e da coleção aparecem em
`indexar.py` e em `buscar.py`, de propósito: são dois processos, e cada um se lê sozinho.
