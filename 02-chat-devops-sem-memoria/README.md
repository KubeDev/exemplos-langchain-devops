# 02 — Chat de terminal sem memoria

Segundo passo depois do `01`. A mesma chamada ao Gemini, agora dentro de um loop: o terminal
fica aberto e voce pode fazer quantas perguntas quiser.

O ponto da aula e este: **um processo continuo nao e uma conversa**. O programa continua
rodando, mas cada pergunta vira uma chamada nova e isolada. O modelo nao sabe o que voce
perguntou na linha anterior.

## O que muda em relacao ao `01`

No `01`, uma pergunta fixa era enviada uma vez e o processo terminava. Aqui a pergunta vem do
teclado, dentro de um `while True`:

```python
while True:
    pergunta = input("Voce: ").strip()
    ...
    responder(pergunta)
```

O que **nao** muda e o conteudo enviado ao modelo: continua sendo o system prompt mais a
pergunta atual, e nada alem disso. O que muda e a forma de compor. No `01` a lista era
escrita na mao a cada chamada; aqui um `ChatPromptTemplate` descreve a ordem das mensagens
uma vez so:

```python
prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessage(SYSTEM_PROMPT),
        ("human", "{pergunta}"),
    ]
)
```

A cada pergunta o template e invocado com um dicionario. A invocacao produz um
`ChatPromptValue`, que vira a lista final de mensagens:

```python
prompt_value = prompt.invoke({"pergunta": pergunta})
mensagens = prompt_value.to_messages()
```

O template e fixo e nao sabe nada do passado. A lista que ele produz nasce e morre dentro de
`responder()`: nada sobrevive entre uma volta do loop e a seguinte.

## Pre-requisitos

- [uv](https://docs.astral.sh/uv/)
- Uma chave da Gemini Developer API

## Como rodar

```bash
cp .env.example .env      # preencha GOOGLE_API_KEY
uv sync
uv run chat-devops-sem-memoria
```

Encerre com linha vazia, `sair` ou `Ctrl+C`.

## Vendo o esquecimento na pratica

Faca uma pergunta e depois uma pergunta de acompanhamento que **nao repete o assunto**:

```
Voce: o que faz o comando kubectl drain?
Voce: e como eu desfaco isso?
```

A segunda pergunta se perde: o modelo nao sabe o que e "isso". Tente tambem:

```
Voce: meu nome e Ana
Voce: qual e o meu nome?
```

Repare no que o programa imprime antes de cada resposta:

```
Prompt produzido: ChatPromptValue
Mensagens enviadas (2 mensagens):
SystemMessage → HumanMessage
```

Sao **sempre 2**, na primeira pergunta e na decima. E essa a prova: o modelo so recebe o que
voce envia, e aqui voce envia apenas a pergunta atual.

## O que este exemplo nao faz

Nao guarda historico, de proposito. Lembrar da conversa e o assunto do `03`, que roda o mesmo
loop e acrescenta um unico slot a este mesmo template — um `MessagesPlaceholder` — para voce
ver esse contador crescer a cada turno.

## Arquivos

```text
src/app.py        modelo, system prompt, template, funcao de resposta e o loop
.env.example      chave da Gemini Developer API
pyproject.toml    dependencias e o comando `chat-devops-sem-memoria`
uv.lock           versoes resolvidas
```
