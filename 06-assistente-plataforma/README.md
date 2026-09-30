# 06 — Assistente de plataforma com Kubernetes via MCP

Este exemplo independente conecta um agente LangChain a um Kubernetes MCP server pronto. A
pessoa descreve em linguagem natural o estado que deseja consultar; o agente escolhe uma das
ferramentas publicadas pelo server e responde com evidências do cluster.

O ponto da aula é este: **um cliente MCP descobre capacidades externas em execução e as entrega
diretamente ao agente**.

## O assistente de plataforma

O programa imprime as oito ferramentas read-only descobertas no endpoint e aguarda o usuário
digitar uma pergunta sobre o cluster:

```python
async with MCPAdapter(MCP_CONFIG) as adapter:
    tools = await adapter.list_tools()

    print("Ferramentas MCP disponíveis:")
    for tool in tools:
        print(f"- {tool.name}")

    agent = create_agent(model=model, tools=tools, system_prompt=SYSTEM_PROMPT)
    pergunta = input("\nPergunta: ")

    resultado = await agent.ainvoke({"messages": [("human", pergunta)]})
```

Não há ferramentas implementadas pela aplicação. Nomes, descrições e schemas chegam do catálogo
MCP e permanecem disponíveis enquanto o adapter está aberto.

## Arquitetura

O projeto não implementa nem inicia um MCP server. Ele se conecta por Streamable HTTP a uma
instância separada do `mcp-server-kubernetes@4.1.6`:

```text
assistente-plataforma                    mcp-server-kubernetes
agente + cliente MCP          HTTP       server MCP
URL + X-MCP-AUTH           ─────────►    kubeconfig + Kubernetes
```

URL e token vêm do ambiente e ficam em `src/tools.py`:

```python
MCP_CONFIG = {
    "mcpServers": {
        "kubernetes": {
            "transport": "http",
            "url": os.getenv(
                "KUBERNETES_MCP_URL", "http://127.0.0.1:3001/mcp"
            ),
            "headers": {"X-MCP-AUTH": KUBERNETES_MCP_TOKEN},
        }
    }
}
```

O server usa o contexto atual do `kubectl`. Execute somente contra um cluster de estudo e mantenha
o modo read-only. O cliente conhece apenas o endpoint, o header de autenticação e o catálogo
publicado; kubeconfig e acesso ao cluster pertencem ao processo do server.

## Pré-requisitos

- Python 3.12 e `uv`;
- Node.js e `npx`;
- `kubectl` configurado para um cluster de estudo;
- chave da API da Anthropic.

Valide o ambiente do server:

```bash
node --version
npx --version
kubectl config current-context
kubectl get pods -n kube-system
```

## Como subir o server HTTP

Depois de preparar o `.env`, inicie o server em um terminal separado:

```bash
./scripts/subir-mcp-kubernetes
```

O script lê `KUBERNETES_MCP_TOKEN` sem imprimir seu valor, mapeia-o para `MCP_AUTH_TOKEN` e inicia
o pacote fixado em `4.1.6`. O bind em `127.0.0.1` evita expor a porta na rede. O modo read-only
limita o catálogo e o server exige o header `X-MCP-AUTH` enviado pelo cliente.

## Como rodar o cliente

```bash
cp .env.example .env
uv sync
uv run assistente-plataforma
```

Compare a resposta com:

```bash
kubectl get pods -n kube-system
```

Os nomes, estados e reinicializações observados devem corresponder ao cluster. A formulação da
resposta continua probabilística; os dados devolvidos pelo server são a evidência da execução.

O system prompt também proíbe consultas a recursos `Secret` e a revelação de credenciais. O modo
read-only evita mutações, mas não transforma todo dado legível em dado seguro para exibir.

## O que este exemplo não faz

- Não implementa, inicia nem encerra um MCP server.
- Não chama `kubectl` diretamente no código Python.
- Não escreve nem remove recursos do cluster.
- Não recebe argumentos de linha de comando; lê uma pergunta por execução.
- Não mantém conversa ou estado entre solicitações.
- Não adiciona middleware, retry, cache, RAG, streaming ou tracing de produção.

## Arquivos

```text
src/app.py                   descoberta das tools e execução do agente
src/tools.py                 configuração do MCP server HTTP (URL e token)
PLANO_TESTE.md               validação manual da demonstração
scripts/subir-mcp-kubernetes inicialização do server HTTP separado
.env.example                 chave da API, modelo, endpoint e token
pyproject.toml               dependências e comando `assistente-plataforma`
```
