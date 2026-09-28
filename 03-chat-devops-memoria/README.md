# 03 — Chat de terminal com memoria, feita na mao

Terceiro passo, logo depois do `02`. O mesmo chat de DevOps, agora lembrando do que foi
dito antes — sem abstracao de historico, sem banco, sem magica. Uma lista guarda
as mensagens anteriores, e um `ChatPromptTemplate` compoe a entrada de cada chamada.

O ponto da aula e este: **o modelo continua sem memoria**. Ele nao guarda nada
entre uma chamada e outra. Quem lembra e o seu codigo, reenviando a conversa
inteira toda vez.

## O que muda em relacao ao `02`

No `02`, o loop ja existia, mas cada pergunta montava a lista do zero:

```python
model.invoke([SystemMessage(SYSTEM_PROMPT), HumanMessage(pergunta)])
```

Aqui existe uma lista que sobrevive entre as voltas do loop e guarda somente os
turnos anteriores:

```python
historico = []
...
resposta = responder(historico, pergunta)
historico.append(HumanMessage(pergunta))
historico.append(resposta)
```

Repare em quem faz o que:

- `main()` e o **dono** do historico — e o unico lugar que anexa mensagens
- `responder()` compoe a entrada e devolve a resposta; nao mexe no historico
- o system prompt e a pergunta atual pertencem ao template, nao ao historico

## Como o prompt e composto

O template descreve a ordem das mensagens que o modelo deve receber:

```python
prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessage(SYSTEM_PROMPT),
        MessagesPlaceholder("historico"),
        ("human", "{pergunta}"),
    ]
)
```

Cada chamada passa um dicionario com o historico e a pergunta atual. A invocacao
produz um `ChatPromptValue`, que pode ser convertido na lista final de mensagens:

```python
prompt_value = prompt.invoke({"historico": historico, "pergunta": pergunta})
mensagens = prompt_value.to_messages()
resposta = model.invoke(mensagens)
```

As responsabilidades ficam separadas:

- o template e a receita fixa de composicao
- o historico e o estado dinamico mantido pela aplicacao
- o `ChatPromptValue` e o resultado de uma invocacao do template
- `mensagens` e a entrada final enviada ao modelo

## Pre-requisitos

- [uv](https://docs.astral.sh/uv/)
- Uma chave da API da Anthropic

## Como rodar

```bash
cp .env.example .env      # preencha ANTHROPIC_API_KEY
uv sync
uv run chat-devops-memoria
```

Encerre com linha vazia, `sair` ou `Ctrl+C`.

## Vendo a diferenca na pratica

Faca uma pergunta e depois uma pergunta de acompanhamento que **nao repete o
assunto**:

```
Voce: o que faz o comando kubectl drain?
Voce: e como eu desfaco isso?
```

Aqui a segunda pergunta e respondida com `kubectl uncordon` — o modelo sabe do
que voce esta falando.

Agora rode a mesma sequencia no `02`:

```bash
cd ../02-chat-devops-sem-memoria && uv run chat-devops-sem-memoria
```

A segunda pergunta se perde: sem historico, "isso" nao existe.

## O comando `limpar`

Digite `limpar` e a lista volta a ficar vazia. Repita a pergunta de acompanhamento
logo em seguida — o modelo perde o contexto na hora. O template ainda acrescenta o
system prompt e a pergunta atual, mas nenhuma mensagem da conversa anterior.

E a forma mais direta de ver que a memoria **e** a lista. Apagou a lista,
esqueceu.

## O que este exemplo nao faz

Tres limites, de proposito:

1. **Morre ao fechar.** A lista vive na memoria do processo. Fechou o terminal,
   acabou a conversa.
2. **E uma conversa so.** Nao ha como manter varias conversas separadas e
   alternar entre elas.
3. **Cresce sem freio.** A lista nunca encolhe. Numa conversa curta isso nao
   incomoda, mas existe um teto — a janela de contexto do modelo — e conversas
   longas esbarram nele.

Nenhum dos tres e resolvido aqui, e isso e intencional: eles sao o motivo pelo
qual o LangChain tem persistencia, threads e estrategias de corte de historico.
Resolver na mao e o proximo passo.

## Arquivos

```
src/app.py        o template, o historico, a funcao de resposta e o loop
.env.example      chave da API e o modelo usado
pyproject.toml    dependencias e o comando `chat-devops-memoria`
```
