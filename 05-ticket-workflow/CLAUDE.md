# Contexto para sessões de IA neste projeto

Leia o `README.md` para entender o que o exemplo faz. Este arquivo é só o que você precisa
saber para **não estragá-lo**.

## Natureza do projeto

Exemplo didático `05` da série `langchain-devops-examples`. A lição é **a chain**:
`prompt | modelo | parser`. O código é lido em sala de aula, projetado numa tela, não
operado em produção.

**Regra de ouro — quando simplicidade e robustez colidirem, vence a simplicidade.** É o
inverso do default e é intencional. Cada abstração a mais é uma coisa a mais para explicar
antes de chegar ao ponto.

## Não adicione sem pedido explícito

`with_structured_output`, `RunnableBranch`, `RunnableParallel`, `RunnablePassthrough`,
LangGraph, `async`/`await`, retry, cache, persistência, testes, camada de serviço,
abstrações "para quando crescer". Todas são boas ideias que **competem com a lição** — e a
seção "O que ficou de fora" do README já explica por que cada uma está ausente. Se
implementar alguma, tire-a da lista.

Em particular: **não há `async` neste projeto**, nem no endpoint. As chains são síncronas e
o FastAPI roda funções `def` num pool de threads sozinho.

## Stack e comandos

- **`uv` sempre**: `uv sync`, `uv add`, `uv run`. Nunca `pip` ou `requirements.txt`.
- `uv.lock` é commitado — a aula precisa ser reproduzível.
- Rodar: `uv run uvicorn src.main:app --reload`

## Armadilhas que já custaram uma execução

- **Não use `temperature`** (nem `top_p`/`top_k`). Sonnet 5 e Opus 4.7+ removeram os
  parâmetros de sampling e devolvem `400`.
- **A triagem precisa responder em DUAS linhas** — uma frase de raciocínio, depois a
  palavra. Pedindo só a palavra, o caso ambíguo é classificado errado de forma consistente:
  sem espaço para deliberar, o modelo crava o domínio mais óbvio. Não "simplifique" isso de
  volta para uma palavra só. (`SYSTEM_TRIAGEM` em `prompts.py`.)
- **Os exemplos few-shot no prompt de triagem não podem ser os payloads de teste.** Já
  foram, e a demo passou sem significar nada — trocados por casos análogos, o erro voltou.
  Os exemplos atuais (kernel/control plane, IndexError pós-release, pool de conexões +
  consulta sem índice, "sistema lento") são deliberadamente diferentes dos quatro cenários.

## Onde fica cada coisa

| Arquivo | Conteúdo | Cuidado |
|---|---|---|
| `chains.py` | as 3 chains e o fluxo — **é o arquivo que vai no projetor** | mantenha enxuto; nada de prosa longa nem formatação de terminal aqui |
| `prompts.py` | só o texto dos system prompts | leia os comentários no topo antes de editar: duas decisões ali custaram uma rodada de validação cada |
| `logs.py` | helpers de formatação | fica separado para não competir com a lição em `chains.py`; as *chamadas* ficam no fluxo, de propósito |
| `schemas.py` | o único Pydantic, o contrato da API | não traga Pydantic para o miolo das chains |
| `tickets.py` | grava os `.md`, Python puro | fora das chains — trocar a saída não deve tocar em LangChain |
| `main.py` | casca HTTP | fina; sem lógica |

## Onde fica o schema

Existe **um** modelo Pydantic, `Alerta`, e ele é o contrato da API. Daí para dentro tudo é
texto. Não introduza Pydantic no miolo das chains — é o exemplo seguinte.

## Modelos

`claude-haiku-4-5` na triagem, `claude-sonnet-5` nos analistas — configuráveis por
`MODELO_TRIAGEM` / `MODELO_ANALISE`. A assimetria **é** conteúdo da aula (a etapa que roda
sempre é a barata). Não unifique sem discutir o impacto pedagógico.

## Credenciais

`ANTHROPIC_API_KEY` **nunca** é gravada em arquivo do repositório. `.env.example` só tem
placeholder; `.env` está no `.gitignore`. Ao validar, peça a chave ao usuário, use apenas no
ambiente do processo e descarte ao final.

## O log é material de aula

`src/logs.py` não é observabilidade — é a interface da apresentação. O log é emitido pelo
próprio fluxo em `chains.py`, linha a linha, para acompanhar o código na ordem em que ele é
lido. Mudança que reduza a legibilidade na tela é regressão, não limpeza. Preserve em
especial o `raciocinio` da triagem: é o que mostra à turma **por que** aquela categoria foi
escolhida.

## Ao mexer nos prompts dos analistas

Os dois analistas recebem **exatamente o mesmo texto de alerta**. A única coisa que os
diferencia são os system prompts em `prompts.py` — inclusive a lista de seções markdown que
cada um produz
(infra: `Recurso afetado` / `Time destino`; dev: `Mudanca suspeita` / `Code owner`). Se essas
listas convergirem, os relatórios convergem e a lição morre. Divergência visível é requisito,
não estética.

A instrução anti-alucinação (copiar trecho literal do log em `## Evidencia`, admitir hipótese
quando não houver) existe porque um ticket com causa raiz inventada custa a hora mais cara da
empresa. O cenário 4 valida isso.

## Cenários

`cenarios.http` e `exemplos/*.json` têm os mesmos payloads, duplicados de propósito (ver
final do README). **Ao editar um cenário, edite os dois.**

O cenário 3 precisa dar `ambos` de forma confiável. Seu payload foi calibrado para ter
evidência concreta nos dois domínios (limite de memória cortado **e** código carregando tudo
em memória). Se ele parar de dar `ambos`, suspeite do payload antes do classificador.
