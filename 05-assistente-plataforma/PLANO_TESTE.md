# Plano de teste — assistente de plataforma

Antes da validação manual, execute `uv run pytest`. A suíte local cobre sanitização e allowlists,
limite do resumo, ausência de conteúdo nos eventos, uma única chamada a `agent.ainvoke()`, ausência
de streaming e separação entre `stdout` e `stderr`, sem acessar cluster ou APIs externas.

## 1. Ambiente

- [ ] `node --version` e `npx --version` respondem.
- [ ] `kubectl config current-context` aponta para um cluster de estudo.
- [ ] `kubectl get pods -n kube-system` responde.
- [ ] `ANTHROPIC_API_KEY` está disponível sem aparecer no terminal.
- [ ] `KUBERNETES_MCP_URL` aponta para o endpoint `/mcp` esperado.
- [ ] Cliente e server usam o mesmo token sem exibi-lo no terminal.
- [ ] `uv sync` conclui sem alterar o lockfile.

## 2. Server HTTP

- [ ] `./scripts/subir-mcp-kubernetes` inicia o processo separado sem imprimir o token.
- [ ] O server está em modo read-only, ligado a `127.0.0.1:3001` e com autenticação.
- [ ] Uma requisição sem `X-MCP-AUTH` recebe `401 Unauthorized`.
- [ ] O processo usa `mcp-server-kubernetes@4.1.6`.

## 3. Descoberta MCP

- [ ] `uv run assistente-plataforma` conecta por Streamable HTTP sem iniciar subprocesso.
- [ ] A saída começa com `Ferramentas MCP disponíveis:`.
- [ ] O catálogo contém exatamente oito ferramentas.
- [ ] Todas as ferramentas vieram de `MCPAdapter.list_tools()`.
- [ ] Nenhuma ferramenta de escrita, remoção ou definida no cliente aparece no inventário.

## 4. Consulta ao Kubernetes

- [ ] Depois de imprimir o catálogo, a aplicação aguarda uma pergunta do usuário.
- [ ] A pergunta é enviada em linguagem natural, sem comando `kubectl`.
- [ ] O agente escolhe uma ferramenta MCP do Kubernetes.
- [ ] A resposta lista pods de `kube-system` com nome, status e reinicializações.
- [ ] Os dados correspondem a `kubectl get pods -n kube-system`.
- [ ] Nenhum recurso do cluster é alterado.

## 5. Observabilidade didática

- [ ] `stdout` contém inventário, prompt `Pergunta:` e resposta final destinada ao usuário.
- [ ] `stderr` contém o recebimento e tamanho da pergunta e o início da decisão do modelo.
- [ ] `stderr` identifica a ferramenta selecionada e seus argumentos sanitizados.
- [ ] Somente os oito nomes esperados podem aparecer; qualquer outro vira `<nome omitido>`.
- [ ] Somente `pods`, `pod` e `kube-system` podem permanecer visíveis nos argumentos; valores dos
  demais campos são omitidos.
- [ ] O fim da ferramenta aparece com resumo estrutural, sem conteúdo do resultado.
- [ ] A resposta final aparece como confirmação e contagem de caracteres, seguida pela duração total.
- [ ] Uma decisão anterior à ferramenta e outra posterior ao resultado ficam observáveis quando o
  agente realiza tool calling.
- [ ] Campos `token`, `authorization`, `api_key`, `password` e `secret` aparecem como `[REDACTED]`.
- [ ] Configuração MCP, headers, mensagens completas, estado do agente e raciocínio do modelo não
  aparecem em nenhuma saída.
- [ ] O system prompt proíbe consultas a `Secret` e a revelação de credenciais.
- [ ] Uma execução com `stdout` e `stderr` redirecionados para arquivos distintos preserva a
  separação dos canais.

## 6. Fronteiras

- [ ] O projeto lê uma pergunta por execução e não recebe argumentos de linha de comando.
- [ ] A execução usa `agent.ainvoke()` e não usa `stream()`, `astream()` ou eventos de streaming.
- [ ] Não há middleware, retry, cache, memória, RAG ou implementação de server.
- [ ] O código não percorre `tool_calls` nem cria `ToolMessage` manualmente.
- [ ] O código Python não executa `kubectl` diretamente.
- [ ] O código Python não contém comando `npx` nem configuração stdio.
- [ ] O valor de `KUBERNETES_MCP_TOKEN` não aparece no script nem no histórico do terminal.
