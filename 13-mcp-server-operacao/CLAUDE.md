# Contexto para sessões de IA neste projeto

Leia o `README.md` antes de alterar este exemplo. Ele registra a demonstração e suas fronteiras.

## Natureza do projeto

Exemplo didático `13` da série `langchain-devops-examples`. A lição é: **a mesma capacidade,
publicada uma vez num MCP server, serve dois clientes** (um agente LangChain e o Claude Code).

O exemplo é autocontido. O código será lido em aula e projetado numa tela. Quando simplicidade e
robustez colidirem, vence a simplicidade.

## Server

- Todo o server fica em `src/servidor.py`, com FastMCP e `@mcp.tool`. Mantenha-o curto.
- Quatro ferramentas, todas de leitura: `listar_droplets`, `consultar_chamado`,
  `buscar_runbook` e `consultar_historico_mudancas`.
- `listar_droplets(regiao)` é a mesma ferramenta do exemplo `09` (`pattern` `^[a-z]{3}[0-9]$`,
  filtro por `region.slug`, retorno resumido por `resumir`). Usa `pydo` e lê `DIGITALOCEAN_TOKEN` dentro da função, para o server subir
  e os testes de dados locais rodarem sem token.
- As ferramentas retornam texto (JSON serializado). Não dependa de conteúdo estruturado: no
  cliente LangChain ele não chega ao modelo.
- O transporte é stdio. Nada de `print` no stdout dentro do server: o log `Ferramenta: ...` vai
  para o stderr.
- Os dados de `dados/` são fictícios e coerentes entre si (incidente `CH-1042`, mudança
  `MUD-311`, runbook `RB-101`). Sem nome de cliente real.

## Clientes

- `src/agente.py` usa `MCPAdapter` de `langchain.mcp`, o mesmo cliente do exemplo `06`. Preserve
  `input()`, uma pergunta por execução e `agent.ainvoke()` sem streaming.
- `MCP_CONFIG` repete a entrada do `.mcp.json`. Mantenha os dois iguais: essa igualdade é o
  argumento da aula.
- O `.mcp.json` nunca contém segredo nem bloco `env`: o server lê `DIGITALOCEAN_TOKEN` do próprio
  `.env`, igual para os dois clientes.

## Testes

`tests/test_servidor.py` testa o server pelo cliente em memória do FastMCP, sem modelo. Os
testes de dados locais rodam offline; o de `listar_droplets` é pulado sem `DIGITALOCEAN_TOKEN`.

## Fronteiras curriculares

- Não declare escopo no retorno, não pagine e não ajuste nível de detalhe: é o exemplo `14`.
- Não adicione ferramenta de escrita nem amplie o escopo do token: é o exemplo `15`.
- Não suba o server por HTTP nem faça deploy.
- Não adicione autenticação, middleware, retry, cache, memória ou streaming.

## Ambiente e credenciais

- Use somente `uv`; dependências por `uv add` e `uv remove`.
- Não use `temperature`, `top_p` ou `top_k`.
- `ANTHROPIC_API_KEY` e `DIGITALOCEAN_TOKEN` nunca entram em arquivo versionado.
- O token do DigitalOcean tem escopo customizado `droplet:read`.
