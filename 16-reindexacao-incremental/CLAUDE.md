# Contexto deste exemplo

Leia o `README.md` e o `CLAUDE.md` da raiz do repositório antes de alterar o projeto.

Este é o exemplo da Aula 08 de Memória e RAG: manter o índice sincronizado com uma base que muda,
pela indexação incremental e pela reindexação total.

- O público é DevOps/cloud, com pouco Python. Cada arquivo é lido em aula de cima a baixo e não
  importa nada de outro arquivo do projeto: `indexar.py` (incremental), `reindexar.py` (total) e
  `buscar.py`. As duas implementações ficam separadas de propósito, para o aluno ver a diferença no
  código. A divisão em chunks e a seleção dos caminhos se repetem nos dois primeiros; não crie
  módulo compartilhado.
- A base é pequena de propósito: os mesmos quatro Markdown em `dados/v1/` e `dados/v2/`, cada v2 com
  uma mudança operacional que aparece na busca. Não existe pasta de fonte separada nem cópia da v1:
  o comando recebe a pasta da versão ou os arquivos. O nome do arquivo é o identificador estável;
  não ponha a versão no nome.
- Um chunk por seção Markdown, com o título no texto do chunk. Sem PDF e sem constante de
  estratégia: a mudança fora da fonte da aula é a troca do modelo, falada, não executada.
- Embeddings locais pelo Ollama (`qwen3-embedding:0.6b`, 1024 dimensões), no `OLLAMA_URL` do
  `.env`. Não há chave de API neste exemplo. O Ollama roda fora do Compose, instalado na máquina.
- Detecção de mudança por documento: hash SHA-256 do arquivo no metadado de cada chunk e ID
  `<coleção>/<arquivo>#<n>`. Documento alterado tem todos os chunks apagados e regravados, sem
  depender de upsert. O ID leva a coleção porque o `id` de `langchain_pg_embedding` é único na
  tabela inteira. `delete` sempre com `collection_only=True`.
- `indexar <pasta | arquivos>`: com uma pasta, a fonte inteira e a remoção do obsoleto; com
  arquivos, só esses documentos e nenhuma remoção. O argumento é obrigatório.
- `reindexar <pasta | arquivos>` grava na `COLECAO`: coleção existente é apagada e regerada no lugar
  (inteira com a pasta, ou só os arquivos passados); coleção nova nasce de uma pasta inteira, e com
  arquivos o comando recusa. Gera os embeddings antes de apagar; regerada inteira, a coleção
  existente passa a registrar o modelo atual no `cmetadata` (o `get_or_create` do LangChain não
  atualiza). A coleção nova é gerada com `COLECAO=base_v2 uv run reindexar dados/v2`, sem tocar o
  `.env`; a troca é a `COLECAO` no `.env`, depois da comparação, e o rollback é voltar a linha. Não
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
