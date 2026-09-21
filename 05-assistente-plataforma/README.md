# 05 — Assistente de plataforma com Kubernetes via MCP

Este exemplo independente conecta um agente LangChain a um Kubernetes MCP server pronto. A
pessoa descreve em linguagem natural o estado que deseja consultar; o agente escolhe uma das
ferramentas publicadas pelo server e responde com evidências do cluster.

O ponto da aula é este: **um cliente MCP descobre capacidades externas em execução e as entrega
diretamente ao agente**.

Durante a única interação, callbacks do LangChain registram em `stderr` os marcos observáveis da
execução. Esses eventos tornam a escolha e o uso da ferramenta visíveis sem expor o estado completo
do agente nem reproduzir manualmente seu ciclo interno.

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
    observability = DidacticObservabilityCallback()
    observability.question_received(pergunta)

    resultado = await agent.ainvoke(
        {"messages": [("human", pergunta)]},
        config={"callbacks": [observability]},
    )
```

Não há ferramentas implementadas pela aplicação. Nomes, descrições e schemas chegam do catálogo
MCP e permanecem disponíveis enquanto o adapter está aberto.

## Evidência didática da execução

O callback registra somente eventos de alto nível:

- pergunta recebida e seu tamanho;
- início de cada decisão do modelo;
- nome da ferramenta e argumentos sanitizados;
- fim da ferramenta e resumo estrutural do resultado;
- confirmação da resposta final, seu tamanho e duração total.

Os eventos usam o prefixo `[observabilidade]` e são escritos em `stderr`. O inventário, o prompt
`Pergunta:` e a resposta destinada ao usuário continuam em `stdout`. Essa separação permite gravar
ou testar os eventos sem misturá-los à resposta normal do programa.

Valores associados a chaves como `token`, `authorization`, `api_key`, `password` e `secret` são
substituídos por `[REDACTED]`. Entre os argumentos, somente os valores fixos `pods`, `pod` e
`kube-system`, necessários ao cenário preparado, podem aparecer; os demais valores são omitidos.
Somente os oito nomes do catálogo esperado podem ser registrados; qualquer outro nome é substituído
por `<nome omitido>`.
Pergunta, resultado da ferramenta e resposta final são resumidos apenas por tipo, quantidade de
itens ou caracteres. O callback não imprime mensagens completas, configuração MCP, headers, estado
do agente, prompts internos ou raciocínio do modelo. Os logs são evidência didática da execução,
não uma solução de tracing para produção.

Exemplo do formato esperado, com conteúdo abreviado:

```text
[observabilidade] pergunta recebida: 97 caracteres
[observabilidade] decisão do modelo iniciada (etapa 1)
[observabilidade] ferramenta iniciada: kubectl_get; argumentos: {"resourceType": "pods", ...}
[observabilidade] ferramenta finalizada: kubectl_get; resultado: texto com 1820 caracteres
[observabilidade] decisão do modelo iniciada (etapa 2)
[observabilidade] resposta final: gerada (486 caracteres)
[observabilidade] duração total: 2.34s
```

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

Execute a suíte unitária local, sem cluster nem credenciais reais, com:

```bash
uv run pytest
```

Compare a resposta com:

```bash
kubectl get pods -n kube-system
```

Os nomes, estados e reinicializações observados devem corresponder ao cluster. A formulação da
resposta continua probabilística; os dados devolvidos pelo server e os eventos do callback são a
evidência da execução.

O system prompt também proíbe consultas a recursos `Secret` e a revelação de credenciais. O modo
read-only evita mutações, mas não transforma todo dado legível em dado seguro para logs.

## O que este exemplo não faz

- Não implementa, inicia nem encerra um MCP server.
- Não chama `kubectl` diretamente no código Python.
- Não escreve nem remove recursos do cluster.
- Não recebe argumentos de linha de comando; lê uma pergunta por execução.
- Não mantém conversa ou estado entre solicitações.
- Não adiciona middleware, retry, cache, RAG, streaming ou tracing de produção.
- Não registra estado completo, segredos, mensagens internas nem chain of thought.

## Arquivos

```text
src/app.py                   descoberta das tools e execução do agente
src/observability.py         callback e sanitização dos eventos didáticos
src/tools.py                 configuração do MCP server HTTP (URL e token)
tests/                       suíte unitária de observabilidade e fluxo mock
PLANO_TESTE.md               validação manual da demonstração
scripts/subir-mcp-kubernetes inicialização do server HTTP separado
.env.example                 chave da API, modelo, endpoint e token
pyproject.toml               dependências e comando `assistente-plataforma`
```
