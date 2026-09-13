# Contexto para sessões de IA neste projeto

Leia o `README.md` para entender o que o exemplo faz. Este arquivo é só o que você precisa
saber para **não estragá-lo**.

## Natureza do projeto

Exemplo didático `01` da série `langchain-devops-examples` — o **primeiro**. A lição são quatro
coisas e nada além delas:

1. `init_chat_model("provider:modelo")` inicializa o modelo
2. `SystemMessage` define o comportamento, `HumanMessage` é a pergunta
3. `invoke()` devolve a resposta inteira, `stream()` devolve pedaço a pedaço
4. `AIMessage` separa conteúdo, uso e metadados da execução

O código é lido em sala de aula, projetado numa tela, não operado em produção. É o menor
programa possível que mostra essas quatro coisas.

As únicas funções nomeadas são `responder()` e `responder_streaming()`. Uma pergunta fixa é
executada uma vez no nível do módulo; preserve a ausência de `main()`, loop e entrada interativa.

**Regra de ouro — quando simplicidade e robustez colidirem, vence a simplicidade.** É o
inverso do default e é intencional. Aqui vale em dobro: este é o primeiro contato do aluno
com LangChain. Cada abstração a mais é uma coisa a mais para explicar antes de chegar ao
ponto.

## A chamada é isolada — e isso é a lição, não um bug

O exemplo envia uma pergunta e termina. **Não adicione loop nem histórico aqui**: interação
contínua e memória pertencem ao exemplo `02` (`02-chat-devops-memoria`).

Se você "consertar" o esquecimento, apaga a razão de o exemplo `02` existir.

## Ambiente e pacotes — `uv`, sem exceção

- **Nunca** `pip`, `python -m venv`, `virtualenv`, `conda`, `poetry` ou `requirements.txt`.
- Dependência entra por `uv add`, sai por `uv remove`. **Não edite `pyproject.toml` à mão** —
  deixe o `uv` escrever, para o `uv.lock` ficar coerente.
- Nunca ative o venv (`source .venv/bin/activate`) nem chame `python` direto. Tudo por
  `uv run`.
- `uv.lock` e `.python-version` são commitados: a aula precisa ser reproduzível.

```bash
uv sync
uv run src/app.py
```

## Não adicione sem pedido explícito

Histórico de conversa, `ChatPromptTemplate`, LCEL, chains, parsers, tools, structured output,
LangGraph, `async`/`await`, retry, cache, testes, tratamento de erro de API, camada de
serviço, abstrações "para quando crescer". **Todas são exemplos posteriores da série.**
Antecipar qualquer uma aqui rouba a aula seguinte e engorda o primeiro contato.

Um `if` a mais neste arquivo é caro. O tamanho é a feature.

## Armadilhas que já custaram uma execução

- **Não adicione parâmetros de sampling.** Escolha de parâmetros não é conteúdo desta aula.
- **`resposta.text` é atributo, não método.** Nas versões atuais do LangChain ele é uma
  propriedade; `resposta.text()` quebra.
- **`stream()` precisa de `flush=True`.** Sem ele o terminal só mostra a resposta no fim, e a
  demonstração de streaming — que é metade da lição — não aparece na tela.
- **Mantenha `automatic_function_calling={"disable": True}` em `invoke()` e `stream()`.** O
  `google-genai 2.22.0` emite um aviso de AFC no caminho `Models.generate_content` mesmo sem
  tools. O argumento funciona na chamada; no construtor, o LangChain o rejeita e produz outro aviso.
- **As duas funções ficam lado a lado, ambas usadas ou não.** `responder_streaming()` existe
  para ser trocada com `responder()` ao vivo, com uma linha. Não apague a que estiver
  inativa: o contraste entre as duas é conteúdo.

## Onde fica cada coisa

Um arquivo só. Isso é deliberado.

| Arquivo | Conteúdo | Cuidado |
|---|---|---|
| `src/app.py` | modelo, system prompt, pergunta e duas formas de consumir a saída — **é o arquivo que vai no projetor** | não fatie em módulos; a lição é caber numa tela |

Não crie `prompts.py`, `logs.py` ou `config.py` aqui. A separação de arquivos aparece a
partir do exemplo `04`, quando passa a haver o que separar.

## Modelo

`gemini-3.8-flash`, inicializado como `google_genai:gemini-3.8-flash`. O formato com prefixo
**é** conteúdo da aula porque separa provider de modelo sem adicionar outra abstração.

## Credenciais

`GOOGLE_API_KEY` **nunca** é gravada em arquivo do repositório. `.env.example` só tem
placeholder; `.env` está no `.gitignore`. Ao validar, peça a chave ao usuário, use apenas no
ambiente do processo e descarte ao final.
