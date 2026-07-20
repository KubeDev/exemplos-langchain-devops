# Contexto para sessões de IA neste projeto

Leia o `README.md` para entender o que o exemplo faz. Este arquivo é só o que você precisa
saber para **não estragá-lo**.

## Natureza do projeto

Exemplo didático `02` da série `langchain-devops-examples`. A lição cabe numa frase: **o
modelo continua sem memória** — ele não guarda nada entre uma chamada e outra. Quem lembra é o
seu código, reenviando a conversa inteira toda vez.

É o contraste direto com o exemplo `01`, que monta a lista do zero a cada pergunta. Aqui a
lista sobrevive ao loop. Só isso muda.

O código é lido em sala de aula, projetado numa tela, não operado em produção.

**Regra de ouro — quando simplicidade e robustez colidirem, vence a simplicidade.** É o
inverso do default e é intencional. Cada abstração a mais é uma coisa a mais para explicar
antes de chegar ao ponto.

## A memória é uma lista Python. Mantenha assim.

Não há framework, banco, store nem abstração de sessão — e a ausência deles **é** o conteúdo.
O aluno precisa ver que "memória de chatbot" é uma lista que cresce, antes de ver qualquer
coisa que esconda isso.

Se você trocar a lista por `RunnableWithMessageHistory`, `InMemoryChatMessageHistory`,
`MemorySaver` ou um checkpointer de LangGraph, a aula acaba: o aluno passa a confiar numa
caixa-preta exatamente no momento em que deveria entender o que tem dentro dela.

## Quem é dono do histórico

`main()` é o **único** lugar que anexa mensagens à lista. `responder()` recebe o histórico,
chama o modelo, imprime e **devolve** o `AIMessage` — não muta nada.

```python
historico.append(HumanMessage(pergunta))     # main() anexa
historico.append(responder(historico))       # main() anexa de novo
```

Essa separação é deliberada e está explicada no README. Se `responder()` passar a fazer
`append`, some a linha que mostra à turma que *pergunta e resposta entram na mesma lista* — e
aparece um efeito colateral escondido numa função que se chama "responder".

## O comando `limpar` é material de aula

`limpar` troca o histórico por um novo (`novo_historico()`) e imprime que o modelo não lembra
mais de nada. Ele existe para você **demonstrar o esquecimento ao vivo**: pergunte o nome,
confirme que ele lembra, limpe, pergunte de novo. Não é uma conveniência de UX — é a prova.

O system prompt entra **uma vez**, na posição 0, e sobrevive ao `limpar` porque
`novo_historico()` o recria. Não anexe o system prompt a cada volta do loop.

## Ambiente e pacotes — `uv`, sem exceção

- **Nunca** `pip`, `python -m venv`, `virtualenv`, `conda`, `poetry` ou `requirements.txt`.
- Dependência entra por `uv add`, sai por `uv remove`. **Não edite `pyproject.toml` à mão** —
  deixe o `uv` escrever, para o `uv.lock` ficar coerente.
- Nunca ative o venv (`source .venv/bin/activate`) nem chame `python` direto. Tudo por
  `uv run`.
- `uv.lock` e `.python-version` são commitados: a aula precisa ser reproduzível.

```bash
uv sync
uv run chat-devops-memoria
```

## Não adicione sem pedido explícito

Janela deslizante, resumo automático do contexto, contagem de tokens, poda do histórico,
persistência em disco ou banco, múltiplas sessões, `ChatPromptTemplate`, LCEL, tools,
structured output, LangGraph, `async`/`await`, retry, cache, testes. **Todas são exemplos
posteriores da série ou ruído.**

O crescimento ilimitado do histórico é uma limitação **conhecida e aceita** aqui: mostrar que
ele cresce sem parar é o gancho para a aula que resolve isso. Não "conserte" antecipando.

## Armadilhas que já custaram uma execução

- **Não use `temperature`** (nem `top_p`/`top_k`). Sonnet 5 e Opus 4.7+ removeram os
  parâmetros de sampling e devolvem `400`.
- **`resposta.text` é atributo, não método.** `resposta.text()` quebra.
- **O `AIMessage` volta inteiro para a lista, não o texto.** Anexar `resposta.text` (uma
  `str`) em vez do objeto quebra a próxima chamada — a API espera mensagens tipadas. É por
  isso que `responder()` devolve `AIMessage` e não `str`.
- **`novo_historico()` devolve lista nova a cada chamada.** Não a transforme em constante de
  módulo: um `HISTORICO_INICIAL` global seria compartilhado entre os resets e acumularia
  mensagens de conversas já apagadas.

## Onde fica cada coisa

Um arquivo só. Isso é deliberado.

| Arquivo | Conteúdo | Cuidado |
|---|---|---|
| `src/app.py` | o system prompt, `novo_historico()`, `responder()` e o loop que anexa — **é o arquivo que vai no projetor** | não fatie em módulos; a lição é caber numa tela e o diff contra o exemplo `01` ser legível a olho nu |

Manter a proximidade com o `01-chat-devops/src/app.py` é requisito: quanto menor a diferença
entre os dois arquivos, mais clara fica a lição. Refatoração que só afete este exemplo afasta
os dois e torna o diff ilegível na aula.

## Modelo

`claude-sonnet-5` por padrão, sobrescrevível por `MODELO` no `.env`, no formato
`provider:modelo`. Igual ao exemplo `01`, de propósito — trocar o modelo não é o assunto aqui.

## Credenciais

`ANTHROPIC_API_KEY` **nunca** é gravada em arquivo do repositório. `.env.example` só tem
placeholder; `.env` está no `.gitignore`. Ao validar, peça a chave ao usuário, use apenas no
ambiente do processo e descarte ao final.
