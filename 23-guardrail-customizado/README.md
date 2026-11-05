# 23 · Guardrail customizado

É o exemplo `22` com uma peça a mais. As mesmas cinco máquinas simuladas, a mesma interface
web, a mesma aprovação humana (`HumanInTheLoopMiddleware`) com prévia, `edit` e `reject`. O que
entra é uma regra do time que nenhum componente pronto conhece:

**máquina do ambiente `prod` só é desligada com a janela de manutenção aberta.**

A regra vira um middleware próprio, `GuardrailManutencao`, que barra a chamada de ferramenta
antes de ela executar e devolve ao modelo o motivo do bloqueio. Ele age na execução, depois da
aprovação: mesmo com a pessoa aprovando, a operação é barrada.

## O que muda em relação ao 22

```bash
diff -r ../22-human-in-the-loop-escrita/src src
```

- `src/guardrail.py` é novo.
- `src/agente.py` ganha o import, o bloco `GUARDRAIL` e `middleware=[APROVACAO, GUARDRAIL]`.
- `src/ferramentas.py` e `src/web.py` são idênticos.

## A janela de manutenção

A janela é uma flag num arquivo texto (`manutencao.txt`, com `aberta` ou `fechada`), indicado
por `ARQUIVO_MANUTENCAO`. O arquivo é lido a cada chamada: editar o arquivo vale sem reiniciar
o servidor. Se o arquivo não puder ser lido, a janela é tratada como fechada.

## As máquinas

O estado fica em memória: reiniciar o servidor volta ao cenário inicial.

| Máquina | Ambiente | Papel | Status |
|---|---|---|---|
| `web-01` | staging | web | active |
| `web-02` | staging | web | active |
| `worker-01` | staging | worker | active |
| `batch-01` | staging | batch | off |
| `api-01` | prod | api | active |

| Arquivo | Papel |
|---|---|
| `src/ferramentas.py` | as máquinas em memória e as quatro ferramentas (igual ao `22`) |
| `src/guardrail.py` | a regra (`janela_aberta`, `verificar`) e o middleware `GuardrailManutencao` |
| `src/agente.py` | o do `22` com o guardrail na lista de middlewares |
| `src/web.py` | a interface do `22`: chat, inventário na barra lateral e o cartão de aprovação |
| `tests/test_guardrail.py` | a regra testada sem agente e sem chave de API |
| `manutencao.txt` | a flag da janela de manutenção |

## Executar

```bash
cp .env.example .env   # preencha ANTHROPIC_API_KEY
uv sync --locked
uv run streamlit run src/web.py
```

| Pedido | O que acontece |
|---|---|
| `Desliga todas as máquinas ligadas` e aprovar | as de staging desligam; a `api-01` é barrada mesmo aprovada, e o motivo aparece em "Chamadas de ferramenta" |
| o mesmo pedido, com `edit` tirando a `api-01` | nada é barrado: a regra só olha o que vai executar |
| editar `manutencao.txt` para `aberta`, pedir `Desliga a api-01` e aprovar | desliga, sem reiniciar o servidor |

O bloqueio chega ao modelo como um `ToolMessage` de erro:

```text
[desligar_maquinas]
Bloqueado pela política de manutenção: api-01 está em prod e a janela de manutenção está fechada. Execute só quando a janela estiver aberta.
```

O texto do modelo varia a cada execução; o bloqueio, não.

## Testes

```bash
uv run pytest
```

A regra (`verificar`) é uma função pura sobre a chamada de ferramenta: testa sem subir o agente.

## O que o exemplo mostra

- **A política vira código.** O modelo pede a chamada, a pessoa aprova, e a regra decide se a
  ferramenta executa. Uma instrução no system prompt é decisão do modelo; o middleware não lê a
  conversa e não é convencido.
- **Aprovação não passa por cima da regra.** O HITL pausa depois do modelo; o guardrail roda
  depois, na execução da ferramenta.
- **Curto-circuito no hook tipo wrap.** O `wrap_tool_call` não chama o `handler` e devolve um
  `ToolMessage` com o motivo. A ferramenta não roda; o modelo lê o motivo e explica a recusa.
- **A regra é por ambiente e só para desligar.** Desligar `web-01` passa com a janela fechada;
  ligar e reiniciar não são afetados.
- **A flag fica fora do código.** Aqui é um arquivo; poderia ser um banco ou um serviço de
  configuração.
