# 01 — Primeira chamada com LangChain

Primeiro exemplo da série. Uma única pergunta DevOps, no menor código possível, para mostrar quatro coisas do LangChain:

1. Inicializar o Gemini com `init_chat_model("provider:modelo")`.
2. Diferenciar `SystemMessage` de `HumanMessage`.
3. Consumir a saída com `invoke()` ou `stream()`.
4. Ler conteúdo, tipo, uso e metadados do `AIMessage`.

O exemplo faz uma chamada isolada. Não existe loop de interação nem histórico.

## Pré-requisitos

- [uv](https://docs.astral.sh/uv/)
- Uma chave da Gemini Developer API

## Como rodar

```bash
cp .env.example .env
uv sync
uv run src/app.py
```

Preencha `GOOGLE_API_KEY` no `.env`. Ao executar, a pergunta fixa é enviada uma vez e o processo termina após a resposta.

## Alternando entre `invoke` e `stream`

No final de `src/app.py`, troque qual chamada está comentada:

```python
responder(pergunta)
# responder_streaming(pergunta)
```

- `responder()` espera a resposta inteira e mostra o conteúdo, o tipo, o uso e os metadados.
- `responder_streaming()` imprime os fragmentos conforme o modelo gera.

## Arquivos

```text
src/app.py        modelo, mensagens, pergunta e invoke/stream
.env.example      chave da Gemini Developer API
pyproject.toml    dependências do exemplo
uv.lock           versões resolvidas
```
