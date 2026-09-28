# Contexto para sessões de IA neste projeto

Leia o `README.md` para entender o que o exemplo faz. Este arquivo é só o que você precisa
saber para **não estragá-lo**.

## Natureza do projeto

Exemplo didático `02` da série `langchain-devops-examples`. A lição cabe numa frase: **um
processo contínuo não é uma conversa** — o terminal fica aberto, mas cada pergunta é uma
chamada isolada e o modelo não sabe o que foi dito antes.

Fica entre o `01` (uma pergunta fixa, uma chamada, fim) e o `03` (o mesmo loop, agora com
histórico). Do `01` herda o modelo e as mensagens; para o `03` entrega o loop e a
composição da entrada por template.

O código é lido em sala de aula, projetado numa tela, não operado em produção.

**Regra de ouro — quando simplicidade e robustez colidirem, vence a simplicidade.** É o
inverso do default e é intencional.

## O esquecimento é a lição, não um bug

A lista de mensagens é produzida pelo template a cada pergunta e descartada no fim.
**Não adicione histórico, `limpar`, `MessagesPlaceholder` nem qualquer estado entre as
voltas do loop**: tudo isso é a lição do `03-chat-devops-memoria`. Se você "consertar" o
esquecimento, apaga a razão de os dois exemplos existirem.

Os prints `Prompt produzido: ChatPromptValue` e `Mensagens enviadas (2 mensagens)` são a
prova na tela. O contador precisa mostrar **sempre 2**, e os dois prints precisam usar o
mesmo formato do `03` — onde o histórico aparece e o contador cresce. Não os remova.

## O template entra aqui, ainda sem nada a variar

`ChatPromptTemplate.from_messages([SystemMessage(SYSTEM_PROMPT), ("human", "{pergunta}")])`
é a receita fixa de composição. `responder()` a invoca com um dicionário e torna visíveis o
`ChatPromptValue` e a lista final de mensagens, antes de chamar o modelo.

O template tem só duas partes e nada de dinâmico além da pergunta — e isso é de propósito.
Ele existe aqui para que o `03` acrescente **uma** coisa, o `MessagesPlaceholder("historico")`,
e o diff entre os dois exemplos seja exatamente a lição da aula.

Não transforme a composição em LCEL nem extraia o template para outro módulo.

## Ambiente e pacotes — `uv`, sem exceção

- **Nunca** `pip`, `python -m venv`, `virtualenv`, `conda`, `poetry` ou `requirements.txt`.
- Dependência entra por `uv add`, sai por `uv remove`. **Não edite dependências do
  `pyproject.toml` à mão** — deixe o `uv` escrever, para o `uv.lock` ficar coerente.
- Nunca ative o venv nem chame `python` direto. Tudo por `uv run`.
- `uv.lock` e `.python-version` são commitados: a aula precisa ser reproduzível.

```bash
uv sync
uv run chat-devops-sem-memoria
```

## Não adicione sem pedido explícito

Histórico, `MessagesPlaceholder`, `stream()`, impressão de metadados do `AIMessage`, LCEL,
tools, `async`/`await`, retry, cache, testes, tratamento de erro de API. Streaming e metadados
já foram a lição do `01`; o resto pertence a exemplos posteriores.

## Armadilhas que já custaram uma execução

- **Não adicione parâmetros de sampling** (`temperature`, `top_p`, `top_k`).
- **`resposta.text` é atributo, não método.** `resposta.text()` quebra.
- **Mantenha `automatic_function_calling={"disable": True}` em `invoke()`.** Sem ele o
  `google-genai` emite um aviso de AFC mesmo sem tools; no construtor, o LangChain o rejeita.

## Onde fica cada coisa

Um arquivo só. Isso é deliberado.

| Arquivo | Conteúdo | Cuidado |
|---|---|---|
| `src/app.py` | modelo, system prompt, `responder()` e o loop — **é o arquivo que vai no projetor** | não fatie em módulos |

Manter a proximidade com `01-chat-devops/src/app.py` e `03-chat-devops-memoria/src/app.py` é
requisito: o diff para cada vizinho deve mostrar só a lição da aula.

## Modelo

`gemini-3.8-flash`, inicializado como `google_genai:gemini-3.8-flash`, igual ao `01`.

## Credenciais

`GOOGLE_API_KEY` **nunca** é gravada em arquivo do repositório. `.env.example` só tem
placeholder; `.env` está no `.gitignore`. Ao validar, peça a chave ao usuário, use apenas no
ambiente do processo e descarte ao final.
