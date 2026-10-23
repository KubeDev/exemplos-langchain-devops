# Contexto deste exemplo

Leia o `README.md` e o `CLAUDE.md` da raiz do repositório antes de alterar o projeto.

Este é o exemplo da Aula 06 de Memória e RAG. A indexação de seis documentos e a busca
vetorial são processos CLI separados. O banco é PostgreSQL com pgvector no Docker Compose.

- O texto extraído dos PDFs e Markdown é enviado somente ao modelo de embedding.
- A busca devolve documentos e distância; não há agente nem modelo de geração.
- Os arquivos são extensos: a primeira indexação cria um `Document` por arquivo. Durante
  a aula, o instrutor substitui `carregar_pdf()` pelo código do roteiro para criar um
  `Document` por página e reindexa. A Aula 07 trata de chunking por conteúdo e tamanho.
- Cada indexação reconstrói a coleção. Atualização incremental pertence à Aula 08.
- Preserve a conferência de modelo e dimensão antes da busca.
- Use `uv`; mantenha a chave da API somente no `.env`, fora do Git.
