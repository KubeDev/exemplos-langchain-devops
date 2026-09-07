# LangChain para DevOps — exemplos

Uma série de exemplos didáticos de LangChain, cada um resolvendo um problema real de DevOps e
ensinando **uma** ideia por vez. São projetos independentes: você pode clonar o repositório
inteiro e rodar só o que interessa.

Os exemplos foram escritos para serem **lidos**, não estendidos. Cada um é o menor código que
demonstra sua ideia — o que falta num exemplo costuma ser o assunto do próximo.

## Os exemplos

| # | Pasta | O que resolve | O que ensina |
|---|---|---|---|
| 01 | [`01-chat-devops`](01-chat-devops) | Uma pergunta DevOps ao Gemini | Modelo, mensagens, `invoke()` vs `stream()` e metadados do `AIMessage` |
| 02 | [`02-chat-devops-memoria`](02-chat-devops-memoria) | O mesmo chat, agora lembrando da conversa | Que o modelo **não** tem memória — quem lembra é o seu código, reenviando a lista |
| 03 | [`03-ticket-workflow`](03-ticket-workflow) | Alerta de observabilidade chega por webhook e vira ticket, roteado para infra ou dev | LCEL: `prompt \| modelo \| parser`, encadeamento e roteamento entre chains |
| 04 | [`04-smart-docker`](04-smart-docker) | Um agente que investiga um projeto e analisa — ou escreve — o Dockerfile dele | Agente de verdade: modelo + ferramentas + loop, onde **quem decide o próximo passo é o modelo** |

A ordem importa. O `02` adiciona interação e memória à chamada isolada do `01`; o `04` só impressiona
depois de ver o fluxo fixo do `03`.

## Pré-requisitos

- [uv](https://docs.astral.sh/uv/) — gerencia Python e dependências
- Python 3.12 (o `uv` instala sozinho, se faltar)
- Uma chave da Gemini Developer API para o exemplo `01`
- Uma chave da API da Anthropic para os exemplos `02` a `04`

## Como rodar qualquer exemplo

Todo exemplo segue o mesmo ritual, sempre **de dentro da pasta dele**:

```bash
cd 01-chat-devops
cp .env.example .env      # preencha GOOGLE_API_KEY
uv sync
```

O comando de execução muda por exemplo:

```bash
cd 01-chat-devops          && uv run src/app.py
cd 02-chat-devops-memoria  && uv run chat-devops-memoria
cd 03-ticket-workflow      && uv run uvicorn src.main:app --reload
cd 04-smart-docker         && uv run smart-docker /caminho/de/um/projeto
```

O `03` sobe uma API — os cenários de teste estão em
[`03-ticket-workflow/cenarios.http`](03-ticket-workflow/cenarios.http) e em `exemplos/*.json`.

Cada pasta tem um `README.md` próprio, com a explicação completa daquele exemplo. Comece por
ele.

## Como o repositório é organizado

Pastas seguem `nn-slug`: número sequencial da aula + nome do projeto. Cada exemplo é
**autocontido** — tem seu próprio `pyproject.toml`, `uv.lock`, `.venv` e `.env`. Não há
workspace, pacote compartilhado nem utilitário comum, de propósito: você pode copiar uma pasta
sozinha para outro lugar e ela roda.

Isso significa dependência duplicada entre os exemplos. É intencional, e o preço é barato
perto de poder tratar cada aula como um projeto independente.

## Sua chave nunca entra no repositório

Cada exemplo tem `.env.example` com placeholder; o `.env` de verdade está no `.gitignore`.
Nenhum arquivo versionado aqui contém credencial.
