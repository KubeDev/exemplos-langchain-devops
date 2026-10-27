# Contexto deste exemplo

Leia o `README.md` e o `CLAUDE.md` da raiz do repositório antes de alterar o projeto.

Este é o exemplo da Aula 08 de Memória e RAG: manter o índice sincronizado com uma base que muda,
pela indexação incremental e pela reindexação total.

- O público é DevOps/cloud, com pouco Python. Cada arquivo é lido em aula de cima a baixo e não
  importa nada de outro arquivo do projeto: `indexar.py` (incremental), `reindexar.py` (total) e
  `buscar.py`. As duas implementações ficam separadas de propósito, para o aluno ver a diferença no
  código. A divisão em chunks e o hash do arquivo se repetem nos dois primeiros; não crie
  módulo compartilhado.
- A base é pequena de propósito: os mesmos quatro Markdown em `dados/v1/` e `dados/v2/`, cada v2 com
  uma mudança operacional que aparece na busca. Não existe pasta de fonte separada nem cópia da v1:
  o `reindexar` recebe a pasta da versão, e o `indexar` recebe um arquivo. O nome do arquivo é o identificador estável;
  não ponha a versão no nome.
- Um chunk por seção Markdown, com o título no texto do chunk. Sem PDF e sem constante de
  estratégia: a mudança fora da fonte da aula é a troca do modelo, falada, não executada.
- Embeddings locais pelo Ollama (`qwen3-embedding:0.6b`, 1024 dimensões), no `OLLAMA_URL` do
  `.env`. Não há chave de API neste exemplo. O Ollama roda fora do Compose, instalado na máquina.
- Detecção de mudança por documento: hash SHA-256 do arquivo no metadado de cada chunk e ID
  `<coleção>/<arquivo>#<n>`. Documento alterado tem todos os chunks apagados e regravados, sem
  depender de upsert. O ID leva a coleção porque o `id` de `langchain_pg_embedding` é único na
  tabela inteira. `delete` sempre com `collection_only=True`.
- `indexar <arquivo>`: um documento por execução, sem laço, lido de cima a baixo (novo, alterado ou
  igual). A consulta ao banco filtra pelo `source` do documento. Não remove nada: o documento que
  saiu da fonte sai no `reindexar` da pasta. A carga inicial é o `reindexar dados/v1`. Não volte a
  aceitar pasta nem vários arquivos no `indexar`.
- `reindexar <pasta>` grava a base inteira na `COLECAO`: coleção existente é apagada com
  `delete_collection()` (os chunks saem junto, pela FK em cascata) e criada de novo com
  `create_collection()`, já com o modelo atual no `cmetadata`; coleção nova é criada ao lado. Gera
  os embeddings antes de apagar. Não volte a aceitar arquivos soltos: reindexar um documento é o
  `indexar`. A lição é que a coleção nova ao lado é melhor que regerar no lugar para a troca. A
  coleção nova é gerada com `COLECAO=base_v2 uv run reindexar dados/v2`, sem tocar o `.env`; a troca é a `COLECAO` no `.env`, depois da comparação, e o rollback é voltar a linha. Não
  acrescente alias, tabela-ponteiro nem renomeação de coleção.
- A coluna `embedding` é `vector(1024)` para a tabela inteira, e os nomes das tabelas são fixos no
  `PGVector`: um modelo com outra dimensão exige outro banco ou outro vector store com tabela
  própria. Recriar as tabelas apaga todas as coleções. Na troca de modelo, `EMBEDDING_MODEL` (código)
  e `COLECAO` (`.env`) trocam juntos, e o rollback volta os dois.
- Não use a indexing API do LangChain (`index()` com `RecordManager`): ela foi para o
  `langchain-classic`, e a aula ensina o mecanismo com gravar com ID, apagar por ID e buscar.
- Não existe teste de busca automatizado nem conjunto de perguntas: o teste como portão da troca
  é etapa de pipeline, do Módulo 09. A comparação antes da troca é o `buscar --colecao`.
- Use `uv`.
