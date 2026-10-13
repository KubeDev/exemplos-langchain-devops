# Contexto deste exemplo

Leia o `README.md` e o `CLAUDE.md` da raiz antes de alterar este projeto.

Este é o exemplo da Aula 03 de Checkpointer. Ele compara o mesmo chat de uso geral com
`InMemorySaver` e `PostgresSaver`, escolhidos por `CHECKPOINTER_BACKEND=memory|postgres` ao
iniciar o processo. Mantenha a interface Jinja igual nos dois modos: o resultado após
reiniciar o Flask deve evidenciar somente a diferença de backend.

- O agente recebe somente a mensagem nova e `thread_config` em `invoke`.
- O seletor e a página leem checkpoints; o navegador não mantém cópia do histórico.
- `InMemorySaver` é compartilhado entre requisições do processo; PostgreSQL usa
  `PostgresSaver.from_conn_string()` e `setup()` na rota.
- Use `uv` e mantenha `.env` fora do Git.
