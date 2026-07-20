# SmartDocker

Agente de IA que investiga um projeto de software e cuida do Dockerfile dele — **analisando o
que existe** ou **escrevendo um do zero** quando não existe.

O agente recebe apenas o caminho de um diretório. A partir daí ele decide sozinho o que ler,
onde procurar e qual dos dois modos usar. Nada disso está codificado em Python: quem decide é
o modelo, a partir do que as ferramentas devolvem.

## Como funciona

1. Lista os arquivos do projeto para entender a estrutura
2. Identifica linguagem e framework lendo os arquivos de dependência — inclusive em
   subdiretórios, já que raramente estão na raiz
3. Procura o Dockerfile e o `.dockerignore`
4. **Escolhe o modo a partir do que encontrou:**
   - **Achou Dockerfile** → avalia pelos 8 critérios e aponta as melhorias
   - **Não achou** → descobre no código o comando de inicialização, a porta e o gerenciador de
     dependências, e **escreve o Dockerfile**
5. Gera um relatório em Markdown, impresso na tela e salvo em arquivo

Essa bifurcação é o ponto do exemplo: o agente toma uma decisão real com base no resultado de
uma ferramenta.

### Critérios de qualidade

Os mesmos oito, usados para julgar um Dockerfile existente ou para construir um novo:

- **Imagem base** — adequada à linguagem/framework, com versão fixada (nunca `latest`)
- **Multi-stage build** — quando aplicável
- **Cache de layers** — dependências copiadas e instaladas antes do código-fonte
- **Usuário não-root** — instrução `USER` definida
- **EXPOSE** — coerente com a porta real da aplicação
- **.dockerignore** — presente no projeto
- **Tamanho da imagem** — variantes `slim`/`alpine` quando possível
- **Segurança** — sem secrets hardcoded, sem pacotes desnecessários

## O log é parte do exemplo

Durante a execução, cada chamada de ferramenta aparece na tela, numerada, com o retorno
pareado:

```
[1] list_directory(dir_path='.')
    [1] -> README.md, .git, src (18 chars)

[2] list_directory(dir_path='src')

[3] file_search(dir_path='.', pattern='Dockerfile*')
    [2] -> migrations, requirements.txt, index.py, models, static, ... (85 chars)
    [3] -> No files found for pattern Dockerfile* in directory .

[4] read_file(file_path='src/requirements.txt')
    [4] -> alembic==1.13.3, Flask==3.0.0, Flask-Migrate==4.0.7, ... (395 chars)
```

Repare que `[2]`, `[3]` e `[4]` são chamadas em paralelo e os retornos chegam fora de ordem —
por isso cada retorno repete o número da sua chamada.

## Tecnologias

- **Python 3.12**
- **LangChain** — `create_agent`, o loop do agente
- **Claude Sonnet** (`claude-sonnet-5`) — o modelo que toma as decisões
- **FileManagementToolkit** — as três ferramentas de sistema de arquivos, prontas

## Pré-requisitos

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) — gerenciador de pacotes e ambientes
- Chave de API da Anthropic

> Este projeto usa **`uv` para tudo**: instalação, ambiente virtual e execução. Não use `pip`,
> `venv` nem ative o ambiente manualmente.

## Instalação

```bash
uv sync
```

Configure a chave de API:

```bash
cp .env.example .env
```

Edite o `.env`:

```
ANTHROPIC_API_KEY=sua-chave-aqui
```

## Uso

```bash
uv run smart-docker /caminho/do/projeto
```

Para escolher o arquivo de saída:

```bash
uv run smart-docker /caminho/do/projeto -o meu-relatorio.md
```

O agente recebe **um diretório local por execução** — não recebe URL de repositório, e analisa
um projeto de cada vez.

## Estrutura do projeto

```
.
├── src/
│   ├── __init__.py
│   ├── app.py            # as três peças (modelo, tools, loop) e o laço de execução
│   ├── prompt.py         # system prompt com a bifurcação dos dois modos
│   ├── tools.py          # as ferramentas, vindas do toolkit
│   └── logs.py           # formatação do log de execução
├── .env.example
├── CLAUDE.md             # contexto para sessões de IA neste projeto
├── PLANO_TESTE.md        # roteiro de validação manual
├── pyproject.toml
├── uv.lock
└── README.md
```

## Exemplo de saída

**Quando o projeto já tem Dockerfile:**

- **Resumo do Projeto** — linguagem, framework, estrutura e dependências
- **Melhorias** — uma seção por problema, com severidade e trecho corrigido
- **Dockerfile Sugerido** — versão completa com tudo aplicado
- **Nota Geral** — adequado · adequado com ressalvas · precisa de ajustes

**Quando não tem:**

- **Resumo do Projeto**
- **O que foi descoberto** — tabela com comando de inicialização, porta, arquivo de
  dependências e versão da linguagem, **e em qual arquivo cada coisa foi encontrada**. O que
  não estiver declarado aparece como "não declarado", com a suposição adotada
- **Dockerfile** — pronto para uso
- **Decisões** — uma linha por critério, justificando a escolha
- **Como usar** — os comandos de build e run daquele projeto
