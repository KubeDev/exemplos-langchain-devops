# 02 — Chat de terminal com memoria, feita na mao

Segundo passo depois do `01`. O mesmo chat de DevOps, agora lembrando do que foi
dito antes — sem framework, sem banco, sem magica. So uma lista de mensagens que
cresce a cada turno.

O ponto da aula e este: **o modelo continua sem memoria**. Ele nao guarda nada
entre uma chamada e outra. Quem lembra e o seu codigo, reenviando a conversa
inteira toda vez.

## O que muda em relacao ao `01`

No `01`, cada pergunta montava a lista do zero:

```python
model.invoke([SystemMessage(SYSTEM_PROMPT), HumanMessage(pergunta)])
```

Aqui existe uma lista que sobrevive entre as voltas do loop:

```python
historico = [SystemMessage(SYSTEM_PROMPT)]   # o system prompt entra UMA vez
...
historico.append(HumanMessage(pergunta))     # a pergunta entra na lista
historico.append(responder(historico))       # a resposta tambem
```

Repare em quem faz o que:

- `main()` e o **dono** do historico — e o unico lugar que anexa mensagens
- `responder()` so envia a lista e devolve a resposta; nao mexe no historico
- o `SYSTEM_PROMPT` fica na **posicao 0**, uma vez so — nao e reenviado a cada
  turno como uma mensagem nova

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

Agora rode a mesma sequencia no `01`:

```bash
cd ../00 && uv run chat-devops
```

A segunda pergunta se perde: sem historico, "isso" nao existe.

## O comando `limpar`

Digite `limpar` e a lista volta a ter so o system prompt. Repita a pergunta de
acompanhamento logo em seguida — o modelo perde o contexto na hora.

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
src/app.py        o historico, a funcao de resposta e o loop
.env.example      chave da API e o modelo usado
pyproject.toml    dependencias e o comando `chat-devops-memoria`
```
