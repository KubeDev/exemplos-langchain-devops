# 01 — Chat de terminal com LangChain

Primeiro exemplo da serie. Um chat de pergunta e resposta no terminal, no menor
codigo possivel, para mostrar tres coisas do LangChain:

1. **Inicializar um modelo** com `init_chat_model("provider:modelo")`
2. **A diferenca entre `SystemMessage` e `HumanMessage`** — o system prompt
   define o comportamento, a mensagem humana e a pergunta
3. **As duas formas de consumir a saida** — `invoke()` (resposta completa) e
   `stream()` (pedaco a pedaco)

O chat e **stateless**: cada pergunta monta a lista de mensagens do zero e nada
e acumulado entre uma pergunta e outra.

## Pre-requisitos

- [uv](https://docs.astral.sh/uv/)
- Uma chave da API da Anthropic

## Como rodar

```bash
cp .env.example .env      # preencha ANTHROPIC_API_KEY
uv sync
uv run chat-devops
```

Encerre com linha vazia, `sair` ou `Ctrl+C`.

## Alternando entre `invoke` e `stream`

Em `src/app.py`, dentro de `main()`, troque qual das duas linhas esta comentada:

```python
responder(pergunta)
# responder_streaming(pergunta)
```

- `responder()` usa `model.invoke(...)` — espera a resposta inteira e imprime
- `responder_streaming()` usa `model.stream(...)` — imprime conforme gera

## O system prompt

A constante `SYSTEM_PROMPT`, no topo de `src/app.py`, impoe um formato fixo de
resposta (comando → o que faz → risco) e limita o assunto a DevOps. Da para ver
o efeito na pratica de dois jeitos:

- perguntando algo fora do escopo (ex.: uma receita de bolo) — o modelo recusa
- esvaziando o `SYSTEM_PROMPT` e repetindo a mesma pergunta — o formato some

## Arquivos

```
src/app.py        modelo, system prompt, as duas funcoes de resposta e o loop
.env.example      chave da API e o modelo usado
pyproject.toml    dependencias e o comando `chat-devops`
```
