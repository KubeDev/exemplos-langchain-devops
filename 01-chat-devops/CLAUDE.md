# Contexto para sessões de IA neste projeto

Leia o `README.md` para entender o que o exemplo faz. Este arquivo é só o que você precisa
saber para **não estragá-lo**.

## Natureza do projeto

Exemplo didático `01` da série `langchain-devops-examples` — o **primeiro**. A lição são três
coisas e nada além delas:

1. `init_chat_model("provider:modelo")` inicializa o modelo
2. `SystemMessage` define o comportamento, `HumanMessage` é a pergunta
3. `invoke()` devolve a resposta inteira, `stream()` devolve pedaço a pedaço

O código é lido em sala de aula, projetado numa tela, não operado em produção. É o menor
programa possível que mostra essas três coisas.

**Regra de ouro — quando simplicidade e robustez colidirem, vence a simplicidade.** É o
inverso do default e é intencional. Aqui vale em dobro: este é o primeiro contato do aluno
com LangChain. Cada abstração a mais é uma coisa a mais para explicar antes de chegar ao
ponto.

## O chat é stateless — e isso é a lição, não um bug

Cada pergunta monta a lista de mensagens do zero. O modelo **não lembra** da pergunta
anterior, e o aluno precisa ver isso acontecer. **Não adicione histórico aqui**: memória é o
exemplo `02` (`02-chat-devops-memoria`), e ela existe como exemplo separado justamente porque
a ausência dela aqui é pedagógica.

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
uv run chat-devops
```

## Não adicione sem pedido explícito

Histórico de conversa, `ChatPromptTemplate`, LCEL, chains, parsers, tools, structured output,
LangGraph, `async`/`await`, retry, cache, testes, tratamento de erro de API, camada de
serviço, abstrações "para quando crescer". **Todas são exemplos posteriores da série.**
Antecipar qualquer uma aqui rouba a aula seguinte e engorda o primeiro contato.

Um `if` a mais neste arquivo é caro. O tamanho é a feature.

## Armadilhas que já custaram uma execução

- **Não use `temperature`** (nem `top_p`/`top_k`). Sonnet 5 e Opus 4.7+ removeram os
  parâmetros de sampling e devolvem `400`.
- **`resposta.text` é atributo, não método.** Nas versões atuais do LangChain ele é uma
  propriedade; `resposta.text()` quebra.
- **`stream()` precisa de `flush=True`.** Sem ele o terminal só mostra a resposta no fim, e a
  demonstração de streaming — que é metade da lição — não aparece na tela.
- **As duas funções ficam lado a lado, ambas usadas ou não.** `responder_streaming()` existe
  para ser trocada com `responder()` ao vivo, com uma linha. Não apague a que estiver
  inativa: o contraste entre as duas é conteúdo.

## Onde fica cada coisa

Um arquivo só. Isso é deliberado.

| Arquivo | Conteúdo | Cuidado |
|---|---|---|
| `src/app.py` | modelo, system prompt, as duas formas de consumir a saída e o loop do terminal — **é o arquivo que vai no projetor** | não fatie em módulos; a lição é caber numa tela |

Não crie `prompts.py`, `logs.py` ou `config.py` aqui. A separação de arquivos aparece a
partir do exemplo `03`, quando passa a haver o que separar.

## Modelo

`claude-sonnet-5` por padrão, sobrescrevível por `MODELO` no `.env`, no formato
`provider:modelo` que o `init_chat_model` espera. O formato com prefixo **é** conteúdo da
aula — é o que mostra que trocar de provedor é trocar uma string.

## Credenciais

`ANTHROPIC_API_KEY` **nunca** é gravada em arquivo do repositório. `.env.example` só tem
placeholder; `.env` está no `.gitignore`. Ao validar, peça a chave ao usuário, use apenas no
ambiente do processo e descarte ao final.
