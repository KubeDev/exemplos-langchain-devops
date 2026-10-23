# Contexto deste exemplo

Leia o `README.md` e o `CLAUDE.md` da raiz antes de alterar este projeto.

Este é o exemplo da Aula 04 de Memória de Longo Prazo com Store. Ele reutiliza o chat Flask
como formato de apresentação, mas usa somente PostgreSQL para checkpointer e Store.

- O checkpointer guarda mensagens por thread; o Store guarda projetos no catálogo e cada decisão como item separado.
- Ana e Bruno são perfis didáticos, não autenticação.
- Todas as funções Python devem ter docstring com os argumentos documentados, inclusive rotas e ferramentas.
- Não adicione RAG, busca vetorial, integrações Cloud ou injeção antecipada de memória no prompt.
- Use `uv` e mantenha `.env` fora do Git.
