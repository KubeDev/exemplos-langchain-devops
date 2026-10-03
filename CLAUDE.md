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
| `01-chat-devops` | chamada isolada: modelo, mensagens, `invoke()` vs `stream()` e metadados do `AIMessage` |
| `02-chat-devops-sem-memoria` | loop sem histórico: cada chamada começa do zero; `ChatPromptTemplate` compõe a entrada |
| `03-chat-devops-memoria` | memória é uma lista; um `MessagesPlaceholder` reenvia essa lista a cada chamada |
| `04-agente-runbook` | runtime mínimo de agente e conhecimento privado inserido diretamente no contexto |
| `05-agente-runbook-tool` | primeira ferramenta registrada no agente e seleção do `runbook_id` pelo modelo |
| `06-assistente-plataforma` | acesso ao Kubernetes em linguagem natural com catálogo descoberto de um MCP server HTTP |
| `07-assistente-plataforma-cli` | execução single shot com argumento, contexto, canais e códigos de saída |
| `08-assistente-plataforma-chat` | conversa com histórico de sessão e resposta progressiva em Streamlit |
| `09-inventario-ec2` | a mesma ferramenta declarada de quatro formas e o esquema que o modelo recebe de cada uma |
| `10-inventario-ec2-testes` | a ferramenta testada sem modelo: invocação direta, pedido de chamada e validação na execução |
| `11-inventario-ec2-colisao` | duas ferramentas com descrições parecidas colidem; a correção é a descrição contrastiva |

**Não antecipe a aula seguinte.** O recurso ausente num exemplo geralmente é o assunto do
próximo, e a ausência é o gancho. Antes de adicionar algo, verifique se ele não é a lição de
um exemplo posterior.

O inverso também vale: **não faça um exemplo convergir para outro**. O `01` é uma chamada
isolada; o `02` introduz o loop sem histórico e a composição por template; o `03` acrescenta
o histórico. Preserve essas fronteiras ao comparar os arquivos.

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

Python `>=3.12` e LangChain permanecem alinhados. A integração de provider é deliberadamente
diferente: os exemplos `01` e `02` usam Gemini; os exemplos `03` a `09` e o `11` continuam com
Anthropic. O `10` não usa modelo. Preserve essa diferença até existir uma decisão explícita de migrar os exemplos
posteriores.

## Layout interno

Código em `src/` em todos os exemplos; o `10` tem também `tests/`. O `01` roda diretamente com `uv run src/app.py`; os
exemplos que expõem comando declaram `[project.scripts]` no `pyproject.toml`.

## Modelos e parâmetros

**Não use `temperature`** (nem `top_p`/`top_k`) nos exemplos. Escolha de sampling não é
conteúdo desta série e já quebrou execuções em providers que não aceitam esses parâmetros.

O `01` fixa Gemini no código para tornar provider e modelo visíveis na primeira aula; o `02`
repete a mesma configuração. Nos demais exemplos, preserve a configuração já existente.

## Os logs são a interface da apresentação

Vários exemplos têm um `logs.py`. Ele não é observabilidade: é o que a turma vê acontecendo na
tela. Mudança que reduza a legibilidade no projetor é regressão, não limpeza — mesmo que
deixe o código mais "limpo".

## Credenciais

Credenciais **nunca** são gravadas no repositório: o `01` e o `02` usam `GOOGLE_API_KEY`; os
demais exemplos continuam usando `ANTHROPIC_API_KEY`; o `09` usa também a configuração
padrão do boto3, e o `10` usa só ela. Cada exemplo tem `.env.example` com placeholder e `.env` no `.gitignore`. Ao validar, use a chave apenas no ambiente do processo.

**Este repositório será aberto ao público.** Antes de commitar qualquer coisa, confirme que
nenhum segredo, caminho pessoal ou nome de cliente entrou no diff. O
`.claude/settings.local.json` está ignorado — mantenha assim.
