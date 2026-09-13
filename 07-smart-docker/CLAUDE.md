# Contexto para sessões de IA neste projeto

Leia o `README.md` para entender o que o exemplo faz. Este arquivo é só o que você precisa
saber para **não estragá-lo**.

## Natureza do projeto

Exemplo didático `07` da série `langchain-devops-examples`. A lição é **o agente**: modelo +
ferramentas + loop, e o fato de que **quem decide o próximo passo é o modelo**, não o código.
É o contraste direto com o exemplo `06`, onde o fluxo é uma chain fixa escrita por você.

O código é lido em sala de aula, projetado numa tela. Ele foi preparado para a **Live 02 —
Construção de Agentes com Python e LangChain**, de nivelamento: o público está vendo tool
calling pela primeira vez.

**Regra de ouro — quando simplicidade e robustez colidirem, vence a simplicidade.** É o
inverso do default e é intencional. Cada abstração a mais é uma coisa a mais para explicar
antes de chegar ao ponto.

## Ambiente e pacotes — `uv`, sem exceção

- **Nunca** `pip`, `python -m venv`, `virtualenv`, `conda`, `poetry` ou `requirements.txt`.
- Dependência entra por `uv add`, sai por `uv remove`. **Não edite `pyproject.toml` à mão** —
  deixe o `uv` escrever, para o `uv.lock` ficar coerente.
- Nunca ative o venv (`source .venv/bin/activate`) nem chame `python` direto. Tudo por
  `uv run`.
- `uv.lock` e `.python-version` são commitados: a aula precisa ser reproduzível.

```bash
uv sync
uv run smart-docker /caminho/do/projeto
```

## Não adicione sem pedido explícito

Tools customizadas com `@tool`, memória conversacional, loop de follow-up, suporte a URL de
repositório, `async`/`await`, retry, cache, testes, camada de serviço, abstrações "para quando
crescer". Todas são boas ideias que **competem com a lição**.

Em particular: **as tools vêm prontas do `FileManagementToolkit`** (`tools.py`, 9 linhas). Isso
é decisão pedagógica, não preguiça — o princípio ensinado é "se existe ferramenta pronta,
use". Escrever `listar/ler/buscar` à mão reinventaria a roda e ainda perderia o sandbox de
`root_dir` que o toolkit já dá de graça.

## Armadilhas que já custaram uma execução

- **Não use `temperature`** (nem `top_p`/`top_k`). O `claude-sonnet-5` removeu os parâmetros de
  sampling e devolve `400`.
- **O raciocínio adaptativo fica no padrão (ligado).** Não passe `thinking`. Como consequência,
  a resposta vem em blocos tipados — por isso `extrair_texto()` lê `content_blocks` e filtra
  os blocos de texto. Não volte a concatenar `content` na mão.
- **O modo duplo é decisão do agente, não `if` em Python.** O `prompt.py` manda buscar o
  Dockerfile e escolher o ramo (analisar / gerar) a partir do resultado da busca. Mover essa
  decisão para o código mata exatamente o que a aula demonstra.
- **O log pareia chamada e retorno pelo `tool_call_id`.** O modelo chama várias ferramentas em
  paralelo e os retornos chegam fora de ordem. Sem o pareamento, a tela vira uma lista de
  respostas órfãs. Já aconteceu; não "simplifique" o dicionário `numero_da_chamada`.
- **Caminhos no log são relativos à raiz do projeto analisado.** Caminho absoluto ocupa três
  linhas no projetor e esconde o que importa (qual arquivo o agente abriu).
- **O warning de depreciação do `langgraph` é silenciado de propósito** no topo do `app.py`,
  antes dos imports que o disparam. Ele aparecia na primeira linha da tela.

## O log é material de aula

`src/logs.py` não é observabilidade — é a interface da apresentação. Como este exemplo **não
escreve tools**, ver a chamada acontecer é a **única** forma de o aluno entender o que é uma
tool. Antes do refactor havia um spinner cobrindo a execução inteira: a aula sobre tool calling
acontecia atrás de uma bolinha girando.

A formatação mora em `logs.py`; as chamadas ficam no fluxo de `app.py`, de propósito, para
acompanhar o código na ordem em que ele é lido. Mudança que reduza a legibilidade na tela é
regressão, não limpeza.

## Onde fica cada coisa

| Arquivo | Conteúdo | Cuidado |
|---|---|---|
| `src/app.py` | as três peças (modelo, tools, loop) e o laço de streaming — **é o arquivo que vai no projetor** | mantenha as três peças em linhas separadas e nomeadas; não troque `ChatAnthropic(...)` pela forma curta `create_agent("claude-sonnet-5", ...)`, que esconde a peça "modelo" |
| `src/prompt.py` | só o system prompt, com a bifurcação do modo duplo | os 8 critérios são a espinha compartilhada pelos dois ramos; mexer em um ramo sem o outro os faz divergir |
| `src/tools.py` | 3 tools do toolkit, 9 linhas | é para ser curto assim |
| `src/logs.py` | formatação do log | ver seção acima |

## Credenciais

`ANTHROPIC_API_KEY` **nunca** é gravada em arquivo do repositório. `.env.example` só tem
placeholder; `.env` está no `.gitignore`. Ao validar, peça a chave ao usuário, use apenas no
ambiente do processo e descarte ao final.

## Alvos da demonstração

A live analisa três repositórios reais do KubeDev, **um por execução** (o agente vê um projeto,
nunca vários):

| Projeto | Stack | Onde ficam as dependências |
|---|---|---|
| `KubeDev/encontros-tech` | Python · Flask 3 · SQLAlchemy · gunicorn | `src/requirements.txt` |
| `KubeDev/kube-news` | Node.js · Express · EJS · Sequelize | `src/package.json` |
| `KubeDev/fake-shop` | Python · Flask · Alembic | `src/requirements.txt` |

**Nenhum dos três tem Dockerfile** — são repositórios de exercício de containerização, onde o
aluno é quem escreve o Dockerfile. Por isso os três exercitam o ramo de **geração**. É também
por isso que o `PLANO_TESTE.md` inclui um quarto cenário com Dockerfile ruim de propósito: sem
ele, metade do modo duplo nunca é testada.

Nos três, o arquivo de dependências está em `src/`, **não na raiz**. O prompt avisa o agente
disso explicitamente. Se ele passar a concluir que o projeto não tem dependências, suspeite
dessa instrução antes de qualquer outra coisa.
