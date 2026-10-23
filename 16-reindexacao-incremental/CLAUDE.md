# Contexto deste exemplo

Leia o `README.md` e o `CLAUDE.md` da raiz do repositório antes de alterar o projeto.

Este é o exemplo da Aula 08 de Memória e RAG: manter o índice sincronizado com uma base que muda,
pela indexação incremental e pela reindexação total.

- O público é DevOps/cloud, com pouco Python. Cada arquivo é lido em aula de cima a baixo e não
  importa nada de outro arquivo do projeto: `indexar.py` (incremental), `reindexar.py` (total) e
  `buscar.py`. As duas implementações ficam separadas de propósito, para o aluno ver a diferença no
  código. A divisão em chunks se repete nos dois primeiros; não crie módulo compartilhado.
- A base é pequena de propósito: quatro Markdown em `versoes/v1/` e `versoes/v2/`, e `dados/` como
  a fonte que o índice lê, commitada igual à v1. Cada v2 traz uma mudança operacional que aparece
  na busca. O nome do arquivo é o identificador estável; não ponha a versão no nome. A versão nova
  entra copiando de `versoes/v2/` para `dados/`, não por flag nos scripts.
- Um chunk por seção Markdown, com o título no texto do chunk. Sem PDF e sem constante de
  estratégia: a mudança fora da fonte da aula é a troca do modelo, falada, não executada.
- Embeddings locais pelo Ollama (`qwen3-embedding:0.6b`, 1024 dimensões), no `OLLAMA_URL` do
  `.env`. Não há chave de API neste exemplo. O Ollama roda fora do Compose, instalado na máquina.
- Detecção de mudança por documento: hash SHA-256 do arquivo no metadado de cada chunk e ID
  `<coleção>/<arquivo>#<n>`. Documento alterado tem todos os chunks apagados e regravados, sem
  depender de upsert. O ID leva a coleção porque o `id` de `langchain_pg_embedding` é único na
  tabela inteira. `delete` sempre com `collection_only=True`.
- `indexar [arquivo ...]`: sem argumento, a pasta inteira e a remoção do obsoleto; com argumento, só
  esses documentos e nenhuma remoção.
- `reindexar [arquivo ...]` grava na `COLECAO`: coleção existente é apagada e regerada no lugar
  (inteira ou só os documentos passados); coleção nova nasce inteira, e com argumento o comando
  recusa. Gera os embeddings antes de apagar; regerada inteira, a coleção existente passa a registrar
  o modelo atual no `cmetadata` (o `get_or_create` do LangChain não atualiza). A coleção nova é gerada
  com `COLECAO=base_v2 uv run reindexar`, sem tocar o `.env`; a troca é a `COLECAO` no `.env`, depois
  da comparação, e o rollback é voltar a linha. Não acrescente alias, tabela-ponteiro nem renomeação de coleção.
- A coluna `embedding` é `vector(1024)` para a tabela inteira: trocar para um modelo com outra
  dimensão exige recriar as tabelas ou usar outro banco.
- Não use a indexing API do LangChain (`index()` com `RecordManager`): ela foi para o
  `langchain-classic`, e a aula ensina o mecanismo com gravar com ID, apagar por ID e buscar.
- Não existe teste de busca automatizado nem conjunto de perguntas: o teste como portão da troca
  é etapa de pipeline, do Módulo 09. A comparação antes da troca é o `buscar --colecao`.
- Use `uv`.
