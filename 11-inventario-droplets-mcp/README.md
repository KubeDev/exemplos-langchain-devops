# 11 · Inventário de Droplets via MCP

O exemplo volta à conta DigitalOcean do `09`, mas o agente **não declara ferramenta nenhuma**.
Ele se conecta a um MCP server próprio, descobre o catálogo que o server publica e registra
todas as ferramentas que encontrar. O código que fala com a DigitalOcean, e o token dela,
ficam no server.

O ponto da aula é este: **quem decide o que o agente pode fazer é o server**. Ferramenta nova
no server aparece no agente na próxima execução, sem mudar uma linha do cliente.

## As ferramentas do server

O server roda em `http://localhost:8000/mcp` (Streamable HTTP) e publica hoje:

| Ferramenta | Argumentos | O que faz |
|---|---|---|
| `list_droplets` | `region` e `status` opcionais | lista os Droplets, resumidos |
| `shutdown_droplet` | `droplet_id` | pede o desligamento gracioso de um Droplet |
| `power_on_droplet` | `droplet_id` | pede a ligação de um Droplet desligado |
| `list_kubernetes_clusters` | — | lista os clusters DOKS, sem kubeconfig |
| `list_database_clusters` | — | lista os bancos gerenciados, sem credenciais |

Duas delas **escrevem** na conta. O agente recebe todas; o único freio é o system prompt, que
pede para só ligar ou desligar quando o usuário pedir explicitamente.

## O agente

`src/app.py` abre o `MCPAdapter`, pede o catálogo e entrega a lista ao `create_agent`:

```python
async with MCPAdapter(MCP_CONFIG) as adapter:
    tools = await adapter.list_tools()
    agent = create_agent(model=model, tools=tools, system_prompt=SYSTEM_PROMPT)
```

Antes de responder, ele imprime as ferramentas descobertas:

```text
Ferramentas MCP disponíveis:
- list_droplets
- shutdown_droplet
- power_on_droplet
- list_kubernetes_clusters
- list_database_clusters
```

A URL vem de `MCP_URL` no `.env`, com `http://localhost:8000/mcp` como padrão.

## Preparação dos Droplets

Os scripts de `setup/` criam e apagam o cenário da aula com o `pydo`. Eles usam o token
`DIGITALOCEAN_TOKEN_SETUP`, com `droplet:create`, `droplet:read`, `droplet:update`,
`droplet:delete`, `tag:create` e `tag:read`. O agente nunca recebe esse token.

```bash
uv run setup/criar_droplets.py     # web-01 e worker-01 em nyc1, batch-01 em sfo3 (desligado)
uv run setup/destruir_droplets.py  # apaga, em todas as regiões, só os Droplets com a tag inventario-droplets
```

| Droplet | Região | Memória | Estado |
|---|---|---|---|
| `web-01` | `nyc1` | 2 GB | `active` |
| `worker-01` | `nyc1` | 1 GB | `active` |
| `batch-01` | `sfo3` | 1 GB | `off` |

Com o `batch-01` desligado, "Ligue o batch-01" faz o agente encadear `list_droplets` (para
achar o id) e `power_on_droplet`.

Droplet desligado continua sendo cobrado: rode o destruir ao terminar.

## Como rodar

Suba o MCP server antes, em `localhost:8000`.

```bash
cp .env.example .env      # preencha ANTHROPIC_API_KEY
uv sync

uv run inventario-droplets-mcp "Quais Droplets estão ativos?"
uv run inventario-droplets-mcp "Quantos clusters Kubernetes e bancos gerenciados existem?"
uv run inventario-droplets-mcp "Ligue o batch-01"
```

## O que este exemplo não faz

- Não pede confirmação humana antes de `shutdown_droplet` ou `power_on_droplet`.
- Não filtra o catálogo no cliente: o agente recebe tudo o que o server publica.
- Não autentica no MCP server.
- Não trata erro de conexão: com o server fora do ar, a execução falha.

## Arquivos

```text
src/app.py                   agente; descobre as ferramentas do MCP server
.env.example                 chave da API, modelo, URL do MCP e token de setup
setup/criar_droplets.py      cria os Droplets de teste
setup/destruir_droplets.py   apaga os Droplets de teste
pyproject.toml               dependências e comando `inventario-droplets-mcp`
```
