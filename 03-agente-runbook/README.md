# 03 — Primeiro agente com conhecimento externo

Terceiro passo depois do `02-chat-devops-memoria`. O exemplo troca a chamada direta ao
modelo pelo runtime de agentes do LangChain e permite executar a mesma pergunta operacional
primeiro sem o runbook privado e depois com o documento carregado no contexto.

O ponto da aula é este: **o modelo só consegue usar conhecimento privado quando a aplicação
o torna parte da entrada**. O arquivo existir no disco não basta.

## O menor runtime possível

O agente é criado sem ferramentas:

```python
agent = create_agent(model=model, tools=[])
```

Nesse estado, o runtime faz somente uma chamada ao modelo. Ainda não existe um ciclo de ação:
sem tools, não há `tool_call`, execução de função nem `ToolMessage`. Essas peças entram no
próximo exemplo.

## A pergunta de controle

O programa usa uma pergunta cujo identificador e procedimento só existem no arquivo local:

```text
Segundo o runbook RB-274, qual é o procedimento para estabilizar a catalog-api
quando o alerta OPS-4821 dispara?
```

Na primeira execução, o campo `{contexto}` fica vazio. O programa imprime também se o
identificador `RB-274` está ou não presente na mensagem de sistema. Essa inspeção é a
evidência determinística; a formulação da resposta do modelo pode variar.

## Carregando o documento

`carregar_documento()` usa `TextLoader` para transformar o Markdown em uma lista de objetos
`Document` e devolver o texto que será inserido no prompt:

```python
loader = TextLoader(RUNBOOK_PATH, encoding="utf-8")
documentos = loader.load()
return "\n\n".join(documento.page_content for documento in documentos)
```

O exemplo imprime o tamanho e os metadados do `Document`. O fluxo do agente permanece único;
para acrescentar o conhecimento externo, basta descomentar uma linha:

```python
contexto = ""
# contexto = carregar_documento()
```

## Pré-requisitos

- [uv](https://docs.astral.sh/uv/)
- Uma chave da API da Anthropic

## Como rodar

```bash
cp .env.example .env      # preencha ANTHROPIC_API_KEY
uv sync
uv run agente-runbook
```

Na primeira execução, mantenha a chamada comentada. Depois, descomente-a e execute novamente.
Como cada cenário começa em um novo processo, a primeira resposta não contamina a segunda.

## O que este exemplo não faz

- Não transforma o runbook em ferramenta.
- Não fragmenta nem indexa o documento.
- Não usa embeddings, vector store ou recuperação seletiva.
- Não escolhe dinamicamente quando consultar o arquivo.

O documento inteiro é inserido no prompt. Isso funciona para um arquivo pequeno e cria a
pergunta que será respondida mais adiante com RAG: o que acontece quando o conhecimento não
cabe inteiro na janela de contexto?

## Arquivos

```text
src/app.py         agente, template, carga do documento e comparação
dados/runbook.md   conhecimento privado fictício usado na demonstração
.env.example       chave da API e modelo
pyproject.toml     dependências e comando `agente-runbook`
```
