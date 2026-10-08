# Plano de teste — MCP server de operação

## 1. Ambiente

- [ ] `uv sync` conclui sem alterar o lockfile.
- [ ] `.env` tem `ANTHROPIC_API_KEY` e `DIGITALOCEAN_TOKEN` sem aparecer no terminal.
- [ ] O token do DigitalOcean tem escopo customizado `droplet:read`.
- [ ] O laboratório está criado: `web-01` e `worker-01` em `nyc1`, `batch-01` em `sfo3`.

## 2. Testes sem modelo

- [ ] `uv run pytest` sem `DIGITALOCEAN_TOKEN`: testes de dados locais passam e `test_listar_droplets_por_regiao` aparece como `skipped`.
- [ ] `uv run pytest` com `DIGITALOCEAN_TOKEN`: todos os testes passam.

## 3. Inspector

- [ ] `npx @modelcontextprotocol/inspector --cli uv run servidor-operacao --method tools/list` lista as quatro ferramentas.
- [ ] A chamada de `consultar_chamado` com `chamado_id=CH-1042` retorna o chamado do `checkout-api`.
- [ ] Na interface web, `listar_droplets` com `regiao=nyc1` retorna `web-01` e `worker-01`, sem `batch-01`; `NYC-1` é recusada pelo esquema.

## 4. Cliente LangChain

- [ ] `uv run agente-operacao` imprime `Ferramentas MCP disponíveis:` com as quatro ferramentas.
- [ ] Depois do catálogo, a aplicação aguarda a pergunta.
- [ ] Com a pergunta sugerida no README, aparecem chamadas `Ferramenta: ...` para chamado, histórico, runbook e Droplets.
- [ ] A resposta cita `MUD-311` (versão 2.14.0, anterior 2.13.4), o runbook `RB-101` e só `web-01` e `worker-01`; `batch-01`, em `sfo3`, fica de fora.
- [ ] Os Droplets citados correspondem ao painel do DigitalOcean.

## 5. Claude Code

- [ ] Sem exportar variável nenhuma, o Claude Code aberto nesta pasta pede aprovação do server `operacao`.
- [ ] `/mcp` mostra o server conectado com as quatro ferramentas.
- [ ] A mesma pergunta produz chamadas às mesmas ferramentas e uma resposta equivalente.

## 6. Fronteiras

- [ ] Nenhuma ferramenta escreve ou altera recursos.
- [ ] O server não escreve no stdout; os logs `Ferramenta: ...` saem pelo stderr.
- [ ] `MCP_CONFIG` e `.mcp.json` têm a mesma entrada `operacao`.
- [ ] Nenhum segredo aparece em `.mcp.json`, código ou histórico do terminal.
- [ ] Não há retorno com escopo declarado, paginação, HTTP, middleware, retry ou cache.
