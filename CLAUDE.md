# Contexto para sessões de IA neste repositório

Este é o **monorepo da série `langchain-devops-examples`**: exemplos didáticos de LangChain
aplicados a DevOps, um por aula, em ordem crescente de complexidade.

Cada exemplo tem seu próprio `CLAUDE.md` com as regras específicas dele — **leia o do exemplo
em que estiver trabalhando**. Este arquivo é só o que vale para a série inteira.

## O código é material de aula

Todo código aqui é lido em sala, projetado numa tela. Não é software de produção e não deve
ser tratado como tal.

**Regra de ouro — quando simplicidade e robustez colidirem, vence a simplicidade.** É o
inverso do default e é intencional. Cada abstração a mais é uma coisa a mais para explicar
antes de chegar ao ponto da aula.

A consequência prática é que **melhorias genuínas de engenharia são regressões aqui** quando
custam clareza: retry, cache, camada de serviço, injeção de dependência, tratamento
abrangente de erro, abstrações "para quando crescer". Nenhuma entra sem pedido explícito.

## Cada exemplo ensina uma coisa — e só ela

| Pasta | Lição |
|---|---|
| `01-chat-devops` | modelo, `SystemMessage`/`HumanMessage`, `invoke()` vs `stream()` |
| `02-chat-devops-memoria` | memória é uma lista que você reenvia; o modelo não lembra |
| `03-ticket-workflow` | LCEL: `prompt \| modelo \| parser`, chains e roteamento |
| `04-smart-docker` | agente: modelo + tools + loop, quem decide é o modelo |

**Não antecipe a aula seguinte.** O recurso ausente num exemplo geralmente é o assunto do
próximo, e a ausência é o gancho. Antes de adicionar algo, verifique se ele não é a lição de
um exemplo posterior.

O inverso também vale: **não faça um exemplo convergir para outro**. A diferença entre
`01-chat-devops/src/app.py` e `02-chat-devops-memoria/src/app.py` precisa continuar pequena e
legível a olho nu — é o diff entre os dois que ensina.

## Convenção de nomes de pasta

`nn-slug`, onde:

- **`nn`** é o número sequencial da aula, dois dígitos, denso, **começando em `01`**
- **`slug`** é o `name` do `pyproject.toml` daquele projeto

Pasta e projeto nunca divergem — se renomear um, renomeie o outro.

**A numeração é densa de propósito, e isso tem um custo conhecido:** inserir uma aula no meio
exige renumerar em cascata todas as posteriores, e ajustar as referências cruzadas nos
`README.md` e `CLAUDE.md` (os exemplos citam uns aos outros pelo número). Ao inserir, procure
por referências antes de considerar o trabalho concluído:

```bash
grep -rn --include='*.md' -E '`0[0-9]`' .
```

## Cada exemplo é autocontido — não existe workspace

Cada pasta tem `pyproject.toml`, `uv.lock`, `.venv` e `.env` próprios. Isso é decisão
deliberada: **o aluno copia uma pasta e roda.**

**Não converta a série num `uv workspace`.** Ele traria um lock único em troca de quebrar
exatamente a propriedade que dá valor ao repo. Dependência duplicada entre exemplos é o preço,
e é barato.

Não há nada compartilhado entre os exemplos — nem pacote comum, nem utilitário, nem
configuração. Se dois exemplos precisam do mesmo código, ele é **duplicado**, não extraído.

## Ambiente e pacotes — `uv`, sem exceção

- **Nunca** `pip`, `python -m venv`, `virtualenv`, `conda`, `poetry` ou `requirements.txt`.
- Dependência entra por `uv add`, sai por `uv remove`. **Não edite `pyproject.toml` à mão** —
  deixe o `uv` escrever, para o `uv.lock` ficar coerente.
- Nunca ative o venv (`source .venv/bin/activate`) nem chame `python` direto. Tudo por
  `uv run`, **de dentro da pasta do exemplo**.
- `uv.lock` e `.python-version` são commitados: a aula precisa ser reproduzível.

**Versões alinhadas em toda a série** (verificado em 2026-07-20): Python `>=3.12`,
`langchain>=1.3.14`, `langchain-anthropic>=1.4.8`. Ao subir a versão de um exemplo, suba a dos
quatro e rode o `PLANO_TESTE.md` de quem tiver um — divergência de versão entre aulas gera a
pergunta "por que esse é diferente?" no meio da apresentação.

## Layout interno

Código em `src/` nos quatro exemplos. Os que rodam como comando declaram
`[project.scripts]` no `pyproject.toml`.

O `03-ticket-workflow` é uma API FastAPI e ainda assim usa `src/` — a consistência entre as
aulas vale mais que a convenção `app/` do framework. **Atenção ao mexer nele:** `app` continua
sendo o nome da instância (`app = FastAPI()`, `@app.post`), então um find-and-replace de `app`
para `src` quebra o projeto. O comando é `uv run uvicorn src.main:app`.

## Modelos e parâmetros

**Não use `temperature`** (nem `top_p`/`top_k`) em nenhum exemplo. Sonnet 5 e Opus 4.7+
removeram os parâmetros de sampling e devolvem `400`. Isso já custou execução mais de uma vez.

Os modelos são configuráveis por variável de ambiente, com default no código. Onde há
assimetria deliberada de modelo (o `03-ticket-workflow` usa Haiku na triagem e Sonnet na
análise), ela **é** conteúdo da aula — não unifique sem discutir o impacto pedagógico.

## Os logs são a interface da apresentação

Vários exemplos têm um `logs.py`. Ele não é observabilidade: é o que a turma vê acontecendo na
tela. Mudança que reduza a legibilidade no projetor é regressão, não limpeza — mesmo que
deixe o código mais "limpo".

## Credenciais

`ANTHROPIC_API_KEY` **nunca** é gravada em arquivo do repositório. Cada exemplo tem
`.env.example` com placeholder e `.env` no `.gitignore`. Ao validar qualquer coisa, peça a
chave ao usuário, use apenas no ambiente do processo e descarte ao final.

**Este repositório será aberto ao público.** Antes de commitar qualquer coisa, confirme que
nenhum segredo, caminho pessoal ou nome de cliente entrou no diff. Saídas de execução
(`tickets/**/*.md` no `03`, `relatorio.md` no `04`) e `.claude/settings.local.json` estão
ignorados — mantenha assim.
