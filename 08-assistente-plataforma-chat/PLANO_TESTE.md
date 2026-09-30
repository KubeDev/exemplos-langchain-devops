# Plano de teste — interface conversacional e retorno parcial

## 1. Ambiente e inicialização

- [ ] `uv sync --locked` conclui sem alterar `uv.lock`.
- [ ] `uv run python -c "import src.app"` não falha por import ausente.
- [ ] `uv run streamlit run src/app.py` inicia e exibe somente o campo de chat.
- [ ] O server separado usa `mcp-server-kubernetes@4.1.6`, bind local, token e modo read-only.

## 2. Histórico e continuidade

- [ ] A primeira pergunta entra em `st.session_state.messages` como `user`.
- [ ] A resposta agregada entra como `assistant` depois do fim do stream.
- [ ] A segunda execução recebe as mensagens dos dois turnos anteriores e a pergunta atual.
- [ ] “Agora mostre somente os que tiveram reinicializações” é interpretada a partir do turno anterior.
- [ ] Recarregar em nova sessão começa sem histórico; nenhum arquivo ou banco é criado.

## 3. Streaming progressivo

- [ ] Mais de um fragmento textual é entregue antes da resposta completa.
- [ ] `st.write_stream` mostra os fragmentos na mensagem atual do assistente.
- [ ] O texto agregado salvo no histórico é igual à concatenação dos fragmentos.
- [ ] A aplicação usa `agent.astream(..., stream_mode="messages")`.

## 4. Separação UI × terminal

- [ ] A UI contém somente mensagens do usuário, respostas textuais e campo de chat.
- [ ] Partes `tool_call_chunk`, conteúdo do nó `tools` e atualizações não aparecem na UI.
- [ ] Falha de execução gera uma mensagem genérica na conversa e somente o tipo da exceção no terminal.
- [ ] Token, headers e configuração MCP não aparecem no terminal.

## 5. Cenário manual da aula

- [ ] Deixar terminal do Streamlit e navegador lado a lado.
- [ ] Perguntar pelos pods de `kube-system` com nome, status e reinicializações.
- [ ] Observar texto chegar progressivamente no navegador.
- [ ] Fazer a pergunta de continuidade sobre os pods reiniciados.
- [ ] Conferir ambas as respostas com `kubectl get pods -n kube-system`.
- [ ] Confirmar que nenhum recurso Kubernetes foi alterado.

## 6. Fronteiras

- [ ] Não há banco, checkpointer, autenticação, aprovação ou auditoria.
- [ ] Não há ferramenta de escrita, chamada direta a `kubectl` ou subprocesso MCP no Python.
- [ ] O código não percorre `tool_calls` nem cria `ToolMessage`.
- [ ] Não há middleware, retry, cache, RAG ou tracing de produção.
