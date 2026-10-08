# 13 — MCP server de operação

Este exemplo independente publica as ferramentas de operação num MCP server próprio e mostra
dois clientes diferentes usando o mesmo server: um agente LangChain e o Claude Code.

O ponto da aula é este: **a mesma capacidade, publicada uma vez, serve dois clientes**. A
ferramenta deixa de ser uma função acoplada a um agente e passa a ser um processo que qualquer
cliente MCP descobre e chama.

## O server

O server inteiro está em `src/servidor.py`. Cada ferramenta é uma função comum com o decorador
`@mcp.tool`; nome, descrição e esquema saem da assinatura e da docstring:

```python
mcp = FastMCP("operacao")


@mcp.tool
def consultar_chamado(chamado_id: str) -> str:
    """Consulta um chamado de operação pelo identificador, como CH-1042.

    Retorna serviço afetado, severidade, status e descrição do chamado.
    """
```

São quatro ferramentas, todas de leitura:

| Ferramenta | Parâmetros | Fonte |
|---|---|---|
| `listar_droplets` | `regiao` opcional, como `nyc1` | API do DigitalOcean (`pydo`) |
| `consultar_chamado` | `chamado_id`, como `CH-1042` | `dados/chamados.json` |
| `buscar_runbook` | `servico` ou `runbook_id`, como `checkout-api` ou `RB-101` | `dados/runbooks.json` |
| `consultar_historico_mudancas` | `servico`, como `checkout-api` | `dados/mudancas.json` |

`listar_droplets` é a mesma ferramenta das aulas anteriores, agora publicada, com o mesmo resumo
de cada Droplet (`nome`, `status`, `regiao`, `tamanho`, `ip_publico`, entre outros). As outras três
leem dados fictícios do domínio de operação: um incidente no `checkout-api` aberto logo depois
de uma implantação, o runbook de rollback do serviço e o histórico de mudanças que mostra a
implantação.

O token do DigitalOcean é lido pelo server, não pelo cliente. Quem chama a ferramenta não
precisa conhecer a credencial.

## Transporte: stdio

O server roda por stdio: o cliente inicia o processo com `uv run servidor-operacao` e conversa
com ele pela entrada e saída padrão. Os dois clientes desta aula sabem iniciar um server
assim a partir da mesma entrada de configuração, sem porta, sem URL e sem processo separado
para subir antes.

Consequência prática: no stdio, o stdout é o canal do protocolo. Por isso o log
`Ferramenta: ...` de cada chamada vai para o stderr.

## Cliente 1: agente LangChain

`src/agente.py` descobre as ferramentas do server e entrega o catálogo ao agente. A
configuração é a mesma entrada que o Claude Code lê no `.mcp.json`:

```python
MCP_CONFIG = {
    "mcpServers": {
        "operacao": {
            "command": "uv",
            "args": ["run", "servidor-operacao"],
        }
    }
}

async with MCPAdapter(MCP_CONFIG) as adapter:
    tools = await adapter.list_tools()
    agent = create_agent(model=model, tools=tools, system_prompt=SYSTEM_PROMPT)
```

O agente não implementa nenhuma ferramenta: nomes, descrições e esquemas chegam do server.

```bash
cp .env.example .env
uv sync
uv run agente-operacao
```

Pergunta sugerida para a demonstração:

```text
O chamado CH-1042 está aberto. Qual mudança recente pode ter causado o problema, qual runbook
devo seguir e quais Droplets estão em nyc1?
```

O laboratório tem Droplets em duas regiões (`web-01` e `worker-01` em `nyc1`, `batch-01` em
`sfo3`); a resposta deve trazer só os de `nyc1`.

A saída mostra o catálogo descoberto, as chamadas que o server recebeu (`Ferramenta: ...`) e a
resposta final.

## Cliente 2: Claude Code

O `.mcp.json` desta pasta registra o mesmo server para o Claude Code. É a mesma entrada do
`MCP_CONFIG`:

```json
{
  "mcpServers": {
    "operacao": {
      "command": "uv",
      "args": ["run", "servidor-operacao"]
    }
  }
}
```

O arquivo não contém segredo. Os dois clientes não passam o token: quem lê `DIGITALOCEAN_TOKEN`
é o server, pelo `.env` desta pasta, do mesmo jeito para os dois. Abra o Claude Code **dentro
desta pasta**, para que ele encontre o `.mcp.json` e o `uv run` encontre o projeto:

```bash
claude
```

Na primeira abertura, o Claude Code pede aprovação para o server do projeto. Depois, `/mcp`
mostra o server `operacao` e suas quatro ferramentas. Faça a mesma pergunta da demonstração.

## Verificação

### MCP Inspector

O Inspector é um cliente MCP de depuração: lista o catálogo e chama ferramentas sem modelo.

```bash
npx @modelcontextprotocol/inspector uv run servidor-operacao
```

O mesmo pelo terminal, em modo CLI:

```bash
npx @modelcontextprotocol/inspector --cli uv run servidor-operacao --method tools/list
npx @modelcontextprotocol/inspector --cli uv run servidor-operacao \
  --method tools/call --tool-name consultar_chamado --tool-arg chamado_id=CH-1042
```

A sintaxe do Inspector muda entre versões; confira a documentação da versão instalada.

### Suíte de testes

`tests/test_servidor.py` testa o server sem modelo. O cliente MCP em memória do FastMCP fala com
o server no mesmo processo, sem subprocesso:

```python
async with Client(mcp) as cliente:
    return await cliente.call_tool(ferramenta, argumentos)
```

```bash
uv run pytest
```

Os testes das ferramentas de dados locais rodam offline. O teste de `listar_droplets` só roda
com `DIGITALOCEAN_TOKEN` no ambiente ou no `.env`; sem ele, aparece como `skipped`. O teste de
região fora do esquema (`NYC-1`) roda offline, porque o server barra o argumento antes de executar a
função.

## Pré-requisitos

- Python 3.12 e `uv`;
- chave da API da Anthropic;
- token do DigitalOcean com escopo customizado `droplet:read`;
- Node.js e `npx`, só para o Inspector;
- Claude Code, só para o segundo cliente.

## O que este exemplo não faz

- Não escreve nem altera recursos: todas as ferramentas são de leitura.
- Não sobe o server por HTTP nem faz deploy dele.
- Não adiciona autenticação, middleware, retry ou cache ao server.
- Não usa streaming nem mantém conversa entre execuções.

## Arquivos

```text
src/servidor.py         MCP server com as quatro ferramentas
src/agente.py           cliente LangChain: descoberta do catálogo e execução do agente
dados/                  chamados, runbooks e histórico de mudanças fictícios
tests/test_servidor.py  ferramentas testadas pelo cliente MCP em memória
.mcp.json               o mesmo server registrado para o Claude Code
.env.example            chave da API, modelo e token do DigitalOcean
PLANO_TESTE.md          validação manual da demonstração
pyproject.toml          dependências e comandos `servidor-operacao` e `agente-operacao`
```
