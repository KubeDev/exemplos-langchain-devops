# 01 · Triagem de incidentes — primeiros passos com LangChain

Um alerta de observabilidade chega por webhook. Uma chain classifica se o incidente é de
infraestrutura ou de desenvolvimento, e a chain do especialista correspondente escreve o
ticket. Quando o alerta toca os dois domínios, os dois especialistas escrevem.

**O que este exemplo ensina cabe numa linha:**

```python
chain = prompt | modelo | parser
```

É a LCEL — *LangChain Expression Language*. O `|` encadeia peças: a saída de uma vira a
entrada da próxima. As três chains aqui têm exatamente essa forma; muda só o prompt.

---

## As três peças

```python
triagem        = prompt_triagem | modelo_triagem | StrOutputParser()
analista_infra = prompt_infra   | modelo_analise | StrOutputParser()
analista_dev   = prompt_dev     | modelo_analise | StrOutputParser()
```

| Peça | O que faz | O que devolve |
|---|---|---|
| `ChatPromptTemplate` | monta as mensagens a partir de um dicionário | lista de mensagens |
| `ChatAnthropic` | chama o modelo | um `AIMessage` |
| `StrOutputParser` | extrai o texto | `str` |

O texto dos prompts fica em `src/prompts.py`, separado do código. É prosa longa, e prosa
longa no meio do código esconde o código — além de ser o que mais muda no dia a dia de um
projeto de LLM.

Sem o parser você receberia um `AIMessage` e teria de lembrar de acessar `.content` toda
vez. Com ele, a chain devolve `str` — e o resto do código lida com texto, que é o que um LLM
consome e produz.

Invocar é `chain.invoke({"alerta": texto})`. Toda chain montada com `|` também ganha
`.batch()`, `.stream()` e `.ainvoke()` de graça.

---

## O fluxo

O LangChain acaba nas três linhas acima. Escolher qual especialista chamar é Python:

```python
categoria = classificar(alerta)          # "infra" | "desenvolvimento" | "ambos"

if categoria == "infra":
    return {"infra": analista_infra.invoke({"alerta": alerta})}
if categoria == "desenvolvimento":
    return {"desenvolvimento": analista_dev.invoke({"alerta": alerta})}

return {                                  # "ambos"
    "infra": analista_infra.invoke({"alerta": alerta}),
    "desenvolvimento": analista_dev.invoke({"alerta": alerta}),
}
```

O LangChain tem primitivas para expressar isso de forma declarativa (`RunnableBranch`,
`RunnableParallel`). Aqui é um `if`, de propósito: um `if` se lê sozinho e não precisa ser
aprendido. Você troca por composição declarativa quando precisar que o pipeline **inteiro**
seja uma peça só — para dar `.batch()` em 500 alertas de uma vez, por exemplo. Até lá, isto
é mais claro.

Os três caminhos devolvem a **mesma forma**: um dicionário `{equipe: relatório}` com uma ou
duas entradas. Quem grava os tickets itera igual nos dois casos, sem saber quantos vieram.

---

## Como rodar

```bash
uv sync
cp .env.example .env      # e preencha ANTHROPIC_API_KEY
uv run uvicorn src.main:app --reload
```

Com o servidor no ar, abra `cenarios.http` e dispare os cenários na ordem (extensão
*REST Client* no VS Code, ou o cliente HTTP do JetBrains). Sem o editor:

```bash
curl -X POST localhost:8000/webhook/alerta \
  -H 'Content-Type: application/json' -d @exemplos/alerta_ambiguo.json
```

Os tickets aparecem em `tickets/infra/` e `tickets/desenvolvimento/`.

> **Leia o terminal.** O log narra o fluxo etapa a etapa — é onde o exemplo se explica:

```
─── ▶ TRIAGEM ──────────────────────────────────────────────────────────
    modelo               claude-haiku-4-5
    raciocinio           Ha reducao de limite de memoria na infraestrutura
                         coincidindo com pico de uso do codigo, ambos plausiveis.
    categoria            ambos

─── ▶ ANALISTA INFRA ───────────────────────────────────────────────────
    modelo               claude-sonnet-5
    tempo                14.8s

─── ▶ ANALISTA DEV ─────────────────────────────────────────────────────
    modelo               claude-sonnet-5
    tempo                15.2s

─── ▶ GRAVAR TICKETS ───────────────────────────────────────────────────
    relatorios           2
```

---

## Os quatro cenários

| # | Cenário | Categoria | Resultado |
|---|---|---|---|
| 1 | Disco cheio no nó | `infra` | 1 ticket em `infra/` |
| 2 | NullPointerException após deploy | `desenvolvimento` | 1 ticket em `desenvolvimento/` |
| 3 | OOMKilled (limite cortado **e** código guloso) | `ambos` | **2 tickets** |
| 4 | Alerta vago, sem log nenhum | `ambos` | 2 tickets, sem evidência |

Os cenários 3 e 4 chegam à mesma categoria por motivos opostos: no 3 há evidência dos
**dois** lados; no 4 não há evidência de lado nenhum. Nos dois casos a resposta certa é
mandar para os dois times — mas por razões diferentes, e o raciocínio no log mostra qual é.

---

## Onde o schema entra (e onde não entra)

Existe **um** modelo Pydantic no projeto, `Alerta`, e ele fica na fronteira da API. O
FastAPI valida o corpo da requisição contra ele e devolve `422` sozinho se o payload não
servir.

Daí para dentro, tudo é texto. `alerta.como_texto()` converte o objeto numa string, os
prompts recebem string, o modelo devolve string, e o ticket é essa string gravada em disco.
Um LLM consome e produz texto — manter o schema só na borda deixa o miolo do exemplo
simples.

O LangChain sabe devolver objetos Pydantic validados (`with_structured_output`), e isso é
útil quando o resultado vai alimentar código em vez de um humano. Fica para o próximo
exemplo.

---

## Um modelo por etapa

A triagem roda em **100% dos alertas** e só precisa devolver uma palavra. Os analistas rodam
em um ou dois casos por alerta e precisam raciocinar sobre logs e escrever um relatório.
Como cada chain é independente, a escolha do modelo é por etapa:

| Etapa | Modelo | Por quê |
|---|---|---|
| triagem | `claude-haiku-4-5` | tarefa curta e fechada, executada sempre |
| analistas | `claude-sonnet-5` | raciocínio sobre logs, saída longa |

Configurável por `MODELO_TRIAGEM` e `MODELO_ANALISE` — troque e compare.

Tempos observados na validação: cenários de rota única ~15s; o cenário `ambos` ~32s, porque
os dois analistas rodam **um depois do outro**.

---

## Três coisas que a validação ensinou

Ficam registradas porque só aparecem quando o código roda de verdade:

1. **`temperature` não existe mais nos modelos novos.** Sonnet 5 e a geração Opus 4.7+
   removeram os parâmetros de sampling; enviá-los devolve `400`. É por isso que ele não
   aparece em `chains.py`.

2. **Pedir "responda com uma palavra" degrada a decisão.** A primeira versão da triagem
   pedia só a categoria, e o caso ambíguo era classificado como `infra` de forma
   consistente — o modelo não tem onde deliberar se só pode emitir um token. Pedindo **duas
   linhas** (uma frase de raciocínio, depois a palavra), os quatro cenários passaram a
   acertar em 12 de 12 execuções. A frase não é enfeite: é o espaço de pensar.

3. **Few-shot que copia o caso de teste não prova nada.** A primeira tentativa de corrigir o
   item 2 foi dar exemplos ao modelo — mas os exemplos eram os próprios payloads de teste.
   Funcionou, e não significava nada: trocados por casos análogos porém diferentes, o erro
   voltou. Foi isso que revelou que o problema real era a falta de espaço para raciocinar,
   não a falta de exemplos.

---

## O que ficou de fora, de propósito

Este é o exemplo `04` de uma série. Cada item abaixo é um exemplo futuro, não uma lacuna:

- **Saída estruturada** (`with_structured_output`) — devolver Pydantic validado em vez de
  texto, para quando o resultado alimenta código.
- **Composição declarativa** (`RunnableBranch`, `RunnableParallel`, `RunnablePassthrough`) —
  e a pergunta que só faz sentido depois de conhecer o `if`: por que eu trocaria um `if` por
  isso? Resposta: para o pipeline inteiro virar uma peça e ganhar `.batch()` e `.stream()`.
- **Execução paralela.** No caso `ambos`, os dois analistas rodam em sequência e o tempo
  dobra. Rodar em paralelo é uma linha (`asyncio.gather`), mas traz `async`/`await` junto —
  e este exemplo não tem nenhum.
- **LangGraph** — estado compartilhado, ciclos, checkpoint, human-in-the-loop.
- **Idempotência.** Um alerta em *flapping* gera um ticket novo a cada oscilação.
- **Retry e observabilidade.** Se a API falhar, o alerta se perde. Não há tracing.

---

## Estrutura

```
src/chains.py    as 3 chains e o fluxo  ← o exemplo é aqui
src/prompts.py   o texto dos system prompts
src/schemas.py   o único Pydantic: o contrato da API
src/tickets.py   grava os .md (Python puro, fora das chains)
src/logs.py      helpers de log
src/main.py      a casca HTTP
cenarios.http    o roteiro da aula
exemplos/        os mesmos payloads, para curl
PLANO_TESTE.md   roteiro de validação manual
CLAUDE.md        contexto para sessões de IA neste projeto
```

O **porquê** de cada decisão mora aqui, no README. O código carrega o *o quê* e
aponta para a seção correspondente — assim uma decisão revista se atualiza num lugar só.

Os payloads estão duplicados entre `cenarios.http` e `exemplos/` de propósito: na aula você
quer o payload e o resultado na mesma tela; em script, quer o arquivo. Ao editar um cenário,
edite os dois.
