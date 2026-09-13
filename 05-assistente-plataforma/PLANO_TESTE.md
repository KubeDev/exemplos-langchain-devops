# Plano de teste — assistente de plataforma

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

## 5. Fronteiras

- [ ] O projeto lê uma pergunta por execução e não recebe argumentos de linha de comando.
- [ ] Não há middleware, retry, cache, memória, RAG ou implementação de server.
- [ ] O código Python não executa `kubectl` diretamente.
- [ ] O código Python não contém comando `npx` nem configuração stdio.
- [ ] O valor de `KUBERNETES_MCP_TOKEN` não aparece no script nem no histórico do terminal.
