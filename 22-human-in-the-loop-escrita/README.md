# 22 · Human-in-the-loop em ações de escrita

Um assistente de operação cuida de cinco máquinas simuladas por uma interface web. Ele pode
listar, ligar, desligar e reiniciar. Ler roda direto; toda ação que muda uma máquina **para
antes de executar**, mostra o que vai mudar e espera a decisão de uma pessoa: aprovar, editar
ou rejeitar. A execução retoma na mesma thread com essa decisão.

O ponto da aula é o `HumanInTheLoopMiddleware`, junto com o checkpointer que guarda a pausa.

## As máquinas

O estado fica em memória: reiniciar o servidor volta ao cenário inicial.

| Máquina | Ambiente | Papel | Status | Hardware | SO |
|---|---|---|---|---|---|
| `web-01` | staging | web | active | 2 vCPU · 4 GB · 80 GB | Ubuntu 24.04 |
| `web-02` | staging | web | active | 2 vCPU · 4 GB · 80 GB | Ubuntu 22.04 |
| `worker-01` | staging | worker | active | 4 vCPU · 8 GB · 160 GB | Ubuntu 24.04 |
| `batch-01` | staging | batch | off | 8 vCPU · 16 GB · 320 GB | Debian 12 |
| `api-01` | prod | api | active | 4 vCPU · 8 GB · 160 GB | Ubuntu 24.04 |

## A configuração

| Ferramenta | Pausa? | Decisões permitidas |
|---|---|---|
| `listar_maquinas` | não (`False` no `interrupt_on`) | — |
| `ligar_maquinas` | sim | `approve` · `reject` |
| `desligar_maquinas` | sim | `approve` · `edit` · `reject` |
| `reiniciar_maquinas` | sim | `approve` · `edit` · `reject` |

As ferramentas de escrita recebem uma lista de nomes. Por isso o `edit` é um ajuste pequeno:
tirar uma máquina do plano. A `description` de cada pausa é a função `previa`, que mostra o
que vai mudar sem executar nada:

```text
desligar_maquinas
web-01 (staging, web) active => off
api-01 (prod, api) active => off
```

| Arquivo | Papel |
|---|---|
| `src/ferramentas.py` | as máquinas em memória e as quatro ferramentas |
| `src/agente.py` | o middleware, a prévia, o checkpointer e as funções `executar` e `retomar` |
| `src/web.py` | só a interface: chat, inventário na barra lateral e o cartão de aprovação |

`executar` e `retomar` não sabem que existe uma web: devolvem a resposta ou a pausa como dado.
A interface só mostra a pausa e devolve a decisão.

## Executar

```bash
cp .env.example .env   # preencha ANTHROPIC_API_KEY
uv sync --locked
uv run streamlit run src/web.py
```

Pedidos que mostram cada decisão:

| Pedido | O que acontece |
|---|---|
| `Quais máquinas rodam Ubuntu 22.04?` | só leitura: responde sem pausar |
| `Desliga todas as máquinas ligadas` | o plano inclui a `api-01` de prod; `edit` tira ela da lista |
| `Reinicia a web-01 e desliga a worker-01` | duas ações na mesma pausa; aprova uma, rejeita a outra com motivo |

## O que este exemplo não faz

- Não guarda a pausa fora do processo: reiniciar o servidor apaga a aprovação pendente.
- Não registra quem aprovou nem mantém trilha de auditoria.
- Não usa `respond`: ele responde no lugar da ferramenta e chega ao modelo como sucesso, então
  não serve para negar uma ação.
