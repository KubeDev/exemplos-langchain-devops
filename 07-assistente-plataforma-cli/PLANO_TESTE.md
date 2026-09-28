# Plano de teste — assistente de plataforma CLI

## 1. Instalação e estrutura

- [ ] `uv sync --locked` conclui sem alterar `uv.lock`.
- [ ] `uv run python -c "import src.app, src.observability, src.tools"` conclui.
- [ ] O comando instalado se chama `assistente-plataforma-cli`.
- [ ] `.env`, `.venv` e caches estão ignorados.

## 2. Contrato de uso

- [ ] `uv run assistente-plataforma-cli --help` termina com código `0`.
- [ ] A ajuda apresenta `pergunta` como posicional e `--namespace` como opção.
- [ ] A ajuda não depende de credenciais nem do MCP server.
- [ ] `uv run assistente-plataforma-cli` termina com código `2`.
- [ ] Uma opção desconhecida termina com código `2`.
- [ ] Não existe opção `--debug`.

## 3. Composição da solicitação

- [ ] Sem `--namespace`, a pergunta chega ao agente sem alteração.
- [ ] Com `--namespace kube-system`, o namespace aparece como contexto adicional.
- [ ] A CLI não aceita verbo, resource type, selector ou output como opções de `kubectl`.
- [ ] A aplicação faz uma única chamada a `agent.ainvoke()`.

## 4. Canais e códigos de retorno

- [ ] Em sucesso, somente a resposta final aparece em `stdout` e o processo retorna `0`.
- [ ] Catálogo MCP, decisões, tools, resumos e duração aparecem em `stderr`.
- [ ] Falta de `ANTHROPIC_API_KEY` ou `KUBERNETES_MCP_TOKEN` aparece em `stderr` e retorna `1`.
- [ ] Falha de conexão, modelo, tool ou formato de resultado retorna `1` sem resposta parcial em `stdout`.
- [ ] Mensagens de exceções externas não aparecem em `stderr`; somente o tipo da falha é registrado.
- [ ] Os testes com mocks cobrem sucesso, falha, uso inválido e separação dos canais.

## 5. Segurança e MCP

- [ ] O server usa `mcp-server-kubernetes@4.1.6` em modo read-only e bind `127.0.0.1`.
- [ ] URL e token vêm do ambiente; o token não aparece no código ou na saída.
- [ ] Campos sensíveis são substituídos por `[REDACTED]`.
- [ ] Valores fora da lista permitida são omitidos dos eventos.
- [ ] Resultado de tool é resumido por estrutura ou tamanho, nunca despejado.
- [ ] O system prompt proíbe alteração, consulta a `Secret` e revelação de credenciais.

## 6. Demonstração integrada

- [ ] O cluster de estudo está ativo e selecionado.
- [ ] `./scripts/subir-mcp-kubernetes` inicia o server em terminal separado.
- [ ] O comando abaixo retorna `0`:

```bash
uv run assistente-plataforma-cli "Liste os pods com reinicializações" --namespace kube-system
```

- [ ] A resposta corresponde a `kubectl get pods -n kube-system`.
- [ ] `stdout` e `stderr` permanecem separados quando redirecionados.
- [ ] Nenhum recurso do cluster é alterado.

## 7. Fronteiras

- [ ] Não há `input()`, chat, histórico, memória ou persistência.
- [ ] Não há `stream()`, `astream()` ou retorno parcial.
- [ ] Não há loop manual sobre `tool_calls` nem construção de `ToolMessage`.
- [ ] O Python não executa `kubectl` ou `npx`.
- [ ] Não há middleware, retry, cache, RAG ou `--debug`.
