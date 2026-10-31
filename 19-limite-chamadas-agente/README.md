# 19 · Limite de chamadas do agente

Um agente acompanha um deploy e só deve responder quando ele terminar. A ferramenta
`consultar_status_deploy` devolve sempre `status provisioning`: o deploy nunca termina, e o
agente consulta de novo a cada volta do loop. É um laço sem progresso.

Sem limite, quem decide parar é o modelo, e o número de consultas muda a cada execução. O
ponto da aula é tirar essa decisão do modelo e colocá-la no código, com dois middlewares
prontos do LangChain. A ferramenta e o system prompt são os mesmos nos dois arquivos; muda só
quem interrompe o laço.

| Arquivo | Middleware | Ao atingir o limite |
|---|---|---|
| `src/limite_modelo.py` | `ModelCallLimitMiddleware(run_limit=3, exit_behavior="end")` | `end`: a execução encerra, sem resposta do modelo |
| `src/limite_ferramenta.py` | `ToolCallLimitMiddleware(tool_name="consultar_status_deploy", run_limit=3)` | `continue`: só a chamada excedida é bloqueada, e o modelo lê o bloqueio e responde |

Os valores dos limites servem à demonstração, não são recomendação.

## Limite de chamadas de modelo

```bash
uv run limite-modelo dpl-4821
```

```text
Pergunta: O deploy dpl-4821 já terminou?

[model] chama consultar_status_deploy({'deploy_id': 'dpl-4821'})
[tools] devolve: deploy dpl-4821: status provisioning
[model] chama consultar_status_deploy({'deploy_id': 'dpl-4821'})
[tools] devolve: deploy dpl-4821: status provisioning
[model] chama consultar_status_deploy({'deploy_id': 'dpl-4821'})
[tools] devolve: deploy dpl-4821: status provisioning
[ModelCallLimitMiddleware.before_model] responde: Model call limits exceeded: run limit (3/3)
```

A última mensagem não vem do modelo: o middleware a coloca no histórico e encerra a
execução antes da quarta chamada. Com `exit_behavior="error"`, ele lança
`ModelCallLimitExceededError` no lugar.

## Limite de chamadas de ferramenta

```bash
uv run limite-ferramenta dpl-4821
```

```text
Pergunta: O deploy dpl-4821 já terminou?

[model] chama consultar_status_deploy({'deploy_id': 'dpl-4821'})
[tools] devolve: deploy dpl-4821: status provisioning
...
[model] chama consultar_status_deploy({'deploy_id': 'dpl-4821'})
[ToolCallLimitMiddleware[consultar_status_deploy].after_model] devolve: Tool call limit exceeded. Do not call 'consultar_status_deploy' again.
[model] responde: Ainda não. O deploy dpl-4821 continua em provisioning...
```

A quarta chamada não executa: o middleware devolve um `ToolMessage` com o motivo, e o modelo
responde com o que já sabe. Com `exit_behavior="end"`, a execução para ali, com uma mensagem
do middleware. Com `"error"`, lança `ToolCallLimitExceededError`.

O log mostra cada mensagem com a etapa que a gerou (`model`, `tools` ou o middleware), lida
do `agent.stream(..., stream_mode="updates")`. A resposta do modelo varia entre execuções:
se ele desistir antes do teto, o limite não chega a disparar.

## Como rodar

```bash
cp .env.example .env      # preencha ANTHROPIC_API_KEY
uv sync

uv run limite-modelo dpl-4821
uv run limite-ferramenta dpl-4821
```

## O que este exemplo não faz

- Não usa `thread_limit`: cada execução é uma pergunta só, sem checkpointer.
- Não trata erro de ferramenta nem repete chamada que falhou.
- Não usa MCP: a ferramenta é local e simulada, para o laço acontecer sempre.

## Arquivos

```text
src/limite_modelo.py         agente com limite de chamadas de modelo
src/limite_ferramenta.py     o mesmo agente com limite de chamadas de ferramenta
.env.example                 chave da API e modelo
pyproject.toml               dependências e comandos `limite-modelo` e `limite-ferramenta`
```
