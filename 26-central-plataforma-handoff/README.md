# 26 · Central da plataforma com handoff

A central da plataforma cloud atende dois assuntos, cada um com um especialista:

| Especialista | Olha para | Pergunta ao usuário | Ferramentas (dados simulados) |
|---|---|---|---|
| **FinOps** | trás: quanto foi gasto, por que a conta subiu, o que está ocioso | se o recurso que causou o pico foi planejado | `custos_por_servico`, `recursos_ociosos`, `estimar_custo_adicional` |
| **Capacidade** | frente: se a aplicação aguenta, onde está o gargalo | quanto tráfego espera em relação ao atual | `uso_atual`, `historico_pico`, `projetar_capacidade` |

Quem atende a conversa fica num campo do estado, o `agente_ativo`, e só uma coisa escreve nele: a **ferramenta de transferência**, que devolve um `Command` gravando o novo especialista. A partir daí, ele conduz a conversa. Não existe retorno: voltar seria uma nova transferência.

Com o campo vazio, quem atende é a **triagem**: uma identidade cujas únicas ferramentas são as duas transferências. Ela não responde o mérito; identifica o assunto e transfere, ou diz que a central não atende aquele assunto.

Um middleware `wrap_model_call` lê o `agente_ativo` a cada chamada de modelo e troca o system prompt e as ferramentas que o modelo enxerga. O agente é um só, e muda de identidade.

Os dados são fictícios e ficam em `src/ferramentas.py`. O exemplo não depende de nenhum outro da série.

| Arquivo | Papel |
|---|---|
| `src/agente.py` | o estado, as ferramentas de transferência, as identidades (triagem, FinOps, Capacidade), o middleware e o agente |
| `src/ferramentas.py` | os dados simulados e as ferramentas dos dois especialistas |
| `src/web.py` | a interface: chat com quem respondeu cada mensagem e, na barra lateral, o estado e a cadeia de transferências da thread |

## Executar

Use Python 3.12, `uv` e uma chave da API da Anthropic.

```bash
cp .env.example .env   # preencha ANTHROPIC_API_KEY
uv sync --locked
uv run streamlit run src/web.py
```

## Percurso da aula

Numa conversa nova:

| Pedido | O que acontece |
|---|---|
| `O kube-news aguenta a campanha da semana que vem?` | a triagem **transfere** para Capacidade, que pergunta quanto tráfego você espera |
| `Esperamos uns 3x o tráfego de hoje.` | Capacidade projeta e aponta os dois gargalos: o limite do HPA e as conexões do banco |
| `E quanto isso vai custar a mais por mês?` | Capacidade **transfere** para FinOps, que responde no mesmo turno; a barra lateral mostra a cadeia triagem → Capacidade → FinOps e as ferramentas trocadas |

Em outras conversas (botão **Nova conversa**):

| Pedido | O que acontece |
|---|---|
| `A conta do kube-news subiu muito em outubro, por quê?` | a triagem transfere para FinOps, que acha o node pool de GPU ocioso em `staging` e pergunta se ele foi planejado |
| `Como eu configuro a VPN do escritório?` | a triagem responde que a central atende custo e capacidade, e **não transfere**; o `agente_ativo` continua vazio |

O texto do modelo varia a cada execução; para onde a conversa é transferida, não. "Chamadas de ferramenta do último turno" mostra a chamada de transferência e a `ToolMessage` que ela devolve.

## O que o exemplo mostra

- **Um campo, um escritor.** Só a ferramenta de transferência escreve o `agente_ativo`, com `Command(update=...)`, por decisão do modelo. O middleware lê o campo a cada chamada de modelo.
- **A triagem não é roteador.** Um roteador é uma etapa fixa antes do agente. Aqui quem escolhe é um agente, chamando uma ferramenta que grava o estado, e a escolha pode ser refeita no meio da conversa.
- **Todas as ferramentas registradas, só algumas visíveis.** O `create_agent` recebe a união das ferramentas, porque é quem executa. O middleware filtra o que o modelo vê; ferramenta fora da lista do `create_agent` dá erro.
- **O histórico passa inteiro.** O especialista novo lê as respostas anteriores no papel de assistente e pode tomá-las como dele. A `ToolMessage` da transferência e uma linha no prompt de cada especialista dizem que aquelas respostas foram de outro.
