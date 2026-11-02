# 23 · Guardrail customizado

Um assistente de operação lista e desliga máquinas simuladas. Três máquinas: `web-01` e
`worker-01` com a tag `staging`, `api-01` com a tag `prod`. Todo desligamento passa por
aprovação humana (`HumanInTheLoopMiddleware`).

O time tem uma regra que nenhum componente pronto conhece: **máquina com a tag `prod` só é
desligada com a janela de manutenção aberta.** A regra vira um middleware próprio,
`GuardrailManutencao`, que barra a chamada de ferramenta antes de ela executar e devolve ao
modelo o motivo do bloqueio. Ele age na execução, depois da aprovação: mesmo com a pessoa
aprovando, a operação é barrada.

A janela é uma flag num arquivo texto (`manutencao.txt`, com `aberta` ou `fechada`), indicado
por `ARQUIVO_MANUTENCAO`. O arquivo é lido a cada chamada: editar o arquivo vale sem reiniciar
o app. Se o arquivo não puder ser lido, a janela é tratada como fechada.

| Arquivo | Papel |
|---|---|
| `src/ferramentas.py` | as máquinas simuladas e as ferramentas `listar_maquinas` e `desligar_maquinas` |
| `src/guardrail.py` | a regra (`janela_aberta`, `verificar`) e o middleware `GuardrailManutencao` |
| `src/agente.py` | modelo, ferramentas, aprovação humana e guardrail juntos no `create_agent` |
| `src/app.py` | chat no terminal: pergunta, aprovação `s/n`, resposta e o status das máquinas |
| `tests/test_guardrail.py` | a regra testada sem agente e sem chave de API |
| `manutencao.txt` | a flag da janela de manutenção |

## Executar

```bash
cp .env.example .env   # preencha ANTHROPIC_API_KEY
uv sync --locked
uv run guardrail-customizado
```

Com o app no ar, edite `manutencao.txt` entre `fechada` e `aberta` e repita o pedido.

```text
Você: Desliga a api-01

[aprovação] desligar_maquinas({'nomes': ['api-01']})
aprovar? [s/n] s
[model] chama listar_maquinas({})
[listar_maquinas] (success)
...
[model] chama desligar_maquinas({'nomes': ['api-01']})
[desligar_maquinas] (error)
Bloqueado pela política de manutenção: api-01 tem a tag prod e a janela de manutenção está fechada. Execute só quando a janela estiver aberta.

[agente]
...

[máquinas] web-01 active · worker-01 active · api-01 active
```

A pausa para aprovação aparece primeiro porque o histórico do turno é impresso só ao fim. O
texto do modelo varia a cada execução; o bloqueio, não.

## Testes

```bash
uv run pytest
```

A regra (`verificar`) é uma função pura sobre a chamada de ferramenta: testa sem subir o agente.

## O que o exemplo mostra

- **A política vira código.** O modelo pede a chamada, a pessoa aprova, e a regra decide se a
  ferramenta executa. Uma instrução no system prompt é decisão do modelo; o middleware não lê a
  conversa e não é convencido.
- **Curto-circuito no hook tipo wrap.** O `wrap_tool_call` não chama o `handler` e devolve um
  `ToolMessage` com o motivo. A ferramenta não roda; o modelo lê o motivo e explica a recusa.
- **A regra é por tag.** Desligar `web-01` passa com a janela fechada.
- **A flag fica fora do código.** Aqui é um arquivo; poderia ser um banco ou um serviço de
  configuração.
