# Contexto para sessões de IA neste projeto

Leia o `README.md` antes de alterar o exemplo. Este é o projeto autocontido da Aula 08: a mesma
capacidade Kubernetes da Aula 06 ganha interface conversacional, histórico de sessão e resposta
progressiva.

## Invariantes didáticas

- A UI contém somente `st.chat_message` e `st.chat_input`; não exiba inventário, status, tool calls,
  resultados de ferramenta, stack traces ou controles adicionais.
- Guarde o histórico real em `st.session_state.messages` e reenvie a lista completa em cada turno.
- A memória é efêmera e limitada à sessão. Não adicione banco, checkpointer, login ou identificação
  de usuário.
- Use o streaming público do agente com `stream_mode="messages"`; renderize somente texto do nó do
  modelo.
- Não percorra `tool_calls`, não crie `ToolMessage` e não implemente manualmente o loop do agente.
- Mantenha callbacks e inventário no stdout/stderr do processo Streamlit.

## Kubernetes e credenciais

- Preserve Streamable HTTP, `X-MCP-AUTH`, bind em `127.0.0.1`, versão `4.1.6` e
  `ALLOW_ONLY_READONLY_TOOLS=true`.
- Nunca execute `kubectl` no código Python nem inicie o server como subprocesso da aplicação.
- Nunca exponha `.env`, token, configuração MCP, conteúdo integral de ferramenta ou mensagens nos
  logs.
- Preserve a proibição de consultar `Secret`, alterar recursos ou revelar credenciais.

## Fronteiras curriculares

Não adicione autenticação, aprovação, auditoria, persistência, middleware, retry, cache, RAG,
observabilidade de produção ou ferramentas de escrita. Essas ausências são nomeadas na aula e
resolvidas em blocos posteriores do curso.

Use somente `uv`; dependências entram por `uv add` e saem por `uv remove`. Execute a aplicação com
`uv run streamlit run src/app.py`. Não use parâmetros de sampling.
