# 16 — Indexação incremental e reindexação total

Este exemplo mantém um índice no pgvector sincronizado com uma base de documentos que muda de
versão. O `indexar` compara cada documento com o que está no banco e grava só a diferença. Quando
muda algo que não está nos arquivos, como o modelo de embedding, o `reindexar` gera de novo sem
olhar o hash, na própria coleção ou numa coleção nova ao lado.

Todos os dados são fictícios e não representam uma operação real.

## Preparação

Use Python 3.12, `uv`, Docker com Compose e o [Ollama](https://ollama.com) instalado e rodando.
Nesta pasta:

```bash
cp .env.example .env
uv sync --locked
docker compose up -d --wait
ollama pull qwen3-embedding:0.6b
```

Os embeddings são gerados localmente pelo `qwen3-embedding:0.6b` (1024 dimensões), sem chave de
API e sem custo por token. A porta local do banco é `55436` e o endereço do Ollama é o `OLLAMA_URL`
do `.env`. A coleção ativa é a `COLECAO` do `.env` (`base_v1` no início). O Compose também sobe o
pgweb em <http://localhost:58436>, já conectado ao banco, para ver os chunks e as coleções.

## A base e as versões

`dados/v1/` e `dados/v2/` têm os mesmos quatro documentos, cada um na sua versão:

| Documento | O que muda da v1 para a v2 |
|---|---|
| `RB-274-catalog-api.md` | o teste dos pods sai do port-forward e passa pelo Service `catalog-api-debug` |
| `RB-381-payments-worker.md` | o reinício dos workers sai de "todos de uma vez" para lotes de 2, com aprovação |
| `RB-905-image-processor.md` | a limpeza do volume sai do `find -delete` e passa pelo `imgproc-admin purge` |
| `ARQ-catalog-api.md` | o cache troca o Redis pelo Valkey, entra a pricing-api e a capacidade passa a ter HPA |

Os comandos recebem o que indexar: uma pasta, que é a fonte inteira, ou arquivos soltos, que são só
esses documentos. O nome do arquivo é o identificador estável do documento, e a versão está no
conteúdo: `dados/v2/RB-274-catalog-api.md` atualiza o RB-274 que entrou pela `dados/v1`.

Cada documento vira um chunk por seção Markdown, com o título no texto do chunk.

## Indexação incremental

```bash
uv run indexar dados/v1                             # a fonte inteira
uv run indexar dados/v2/RB-274-catalog-api.md       # só esse documento
```

Para cada documento, calcula o hash SHA-256 do arquivo e compara com o hash gravado no metadado dos
chunks daquele documento:

| Situação | O que acontece |
|---|---|
| Novo | divide, gera embedding e grava |
| Alterado | apaga todos os chunks antigos do documento e grava os novos |
| Igual | nada, e nenhuma chamada ao modelo |
| Removido | está no índice e não está na pasta: os chunks são apagados |

A remoção só acontece quando o argumento é uma pasta, porque só a fonte inteira diz o que saiu dela.
O ID de cada chunk é `<coleção>/<arquivo>#<n>`. Rodar de novo sem mudar nada termina com todos os
documentos iguais: o script é idempotente.

```bash
uv run indexar dados/v1
uv run buscar "Posso usar port-forward para testar os pods da catalog-api?"   # a v1
uv run indexar dados/v2/RB-274-catalog-api.md
uv run buscar "Posso usar port-forward para testar os pods da catalog-api?"   # a v2
uv run indexar dados/v1                                                       # o RB-274 volta para a v1
```

## Ver o que foi gravado

Abra <http://localhost:58436>. Na aba *Query*, o ID, o hash e a versão de cada chunk:

```sql
SELECT id, cmetadata->>'hash' AS hash, left(document, 60) AS inicio
FROM langchain_pg_embedding
ORDER BY id;
```

Rode depois de cada `indexar`: o documento alterado troca de hash e de texto, os iguais
continuam como estavam. Para ver as coleções lado a lado, depois do `reindexar` numa coleção
nova:

```sql
SELECT c.name AS colecao, c.cmetadata->>'model' AS modelo, count(*) AS chunks
FROM langchain_pg_embedding e
JOIN langchain_pg_collection c ON c.uuid = e.collection_id
GROUP BY c.name, modelo;
```

## Reindexação total

O hash protege a fonte, não a forma de transformá-la em vetor. Se o modelo de embedding mudar, os
arquivos continuam iguais e o `indexar` não reprocessa nada. O `reindexar` gera de novo sem olhar o
hash, na coleção apontada pela `COLECAO`:

| `COLECAO` aponta para | `uv run reindexar dados/v1` | `uv run reindexar <arquivo>` |
|---|---|---|
| uma coleção que já existe | apaga e regera a base inteira no lugar e registra o modelo atual na coleção | apaga e regera só esses documentos, como um documento com índice suspeito |
| uma coleção nova | gera a base inteira ao lado da anterior, que continua intacta | recusa: coleção nova nasce de uma pasta inteira |

Os embeddings são gerados antes de apagar: se o modelo falhar, a coleção continua como estava. Troca
de modelo é sempre a base inteira: regerar um documento só deixaria modelos misturados na coleção.
Apagar e regerar serve para base pequena e janela aceitável. A coleção nova ao lado serve quando a
base é grande, o agente está em produção ou a mudança precisa ser comparada antes de valer.

## Coleção nova, comparação, troca e volta

```bash
COLECAO=base_v2 uv run reindexar dados/v2        # a variável só no comando: a ativa continua base_v1
uv run buscar "Como reiniciar os workers do payments-worker depois da rotação da credencial do broker?"
uv run buscar "Como reiniciar os workers do payments-worker depois da rotação da credencial do broker?" --colecao base_v2
```

Sem `--colecao`, o `buscar` usa a coleção ativa. A variável passada na linha de comando vale só para
aquele comando e prevalece sobre o `.env`. Depois da comparação, a troca é a `COLECAO` no `.env`, e o
rollback é voltar a linha. Na troca de modelo, o modelo está no código (`EMBEDDING_MODEL`) e a coleção
no `.env`: os dois trocam juntos, e o rollback volta os dois.

Todas as coleções ficam na mesma tabela, e a coluna do vetor tem a dimensão fixada na criação
(`vector(1024)`), e os nomes das tabelas são fixos no `PGVector`. Um modelo com outra dimensão não
cabe numa coleção nova ao lado: exige outro banco ou outro vector store, com tabela própria.

O `buscar` confere o modelo de embedding registrado na coleção e recusa a consulta com outro
modelo: é a mensagem que pede a reindexação quando o modelo muda.

A leitura do que está gravado é a única parte específica do pgvector: o `indexar` e o `reindexar`
leem IDs e metadado por SQL. Gravar com ID e apagar por ID são operações do vector store do
LangChain.

## Um arquivo, uma leitura

Cada comando é um arquivo que se lê sozinho, de cima a baixo, sem importar nada de outro arquivo do
projeto. Por isso a divisão em chunks e a seleção dos caminhos aparecem em `indexar.py` e em
`reindexar.py`. A repetição é de propósito. Ao mudar uma delas, mude nos dois lugares.
