# 04 — Primeira ferramenta no agente

Quarto passo depois do `03-agente-runbook`. O exemplo mantém o domínio dos runbooks,
mas deixa de inserir o documento no system prompt. O agente recebe uma ferramenta capaz
de carregar o runbook solicitado e decide chamá-la com o identificador presente na pergunta.

O ponto da aula é este: **a aplicação oferece a capacidade; o agente escolhe usá-la e
preenche seu parâmetro**.

## A ferramenta

`src/tools.py` concentra a criação da ferramenta e o catálogo de documentos permitidos:

```python
RUNBOOKS = {
    "RB-274": RUNBOOKS_PATH / "RB-274.md",
    "RB-381": RUNBOOKS_PATH / "RB-381.md",
    "RB-905": RUNBOOKS_PATH / "RB-905.md",
}


@tool
def consultar_runbook(runbook_id: str) -> str:
    """Carrega um runbook interno pelo identificador informado na pergunta."""
```

O modelo recebe o nome, a descrição e o schema `runbook_id: string`. Ele não recebe acesso
livre ao filesystem: a aplicação controla quais identificadores existem e a qual arquivo
cada um corresponde.

## A pergunta controlada

Os três cenários usam exatamente a mesma expressão e a mesma tarefa. Somente o identificador
muda:

```text
Segundo o runbook RB-274, qual é o procedimento para estabilizar o serviço?
Segundo o runbook RB-381, qual é o procedimento para estabilizar o serviço?
Segundo o runbook RB-905, qual é o procedimento para estabilizar o serviço?
```

No código existe um único template:

```python
PERGUNTA = "Segundo o runbook {runbook_id}, qual é o procedimento para estabilizar o serviço?"
```

Essa padronização isola a variável observada: o ID que o agente envia para a ferramenta.

## Configuração do agente

`src/app.py` registra a ferramenta diretamente no agente:

```python
agent = create_agent(
    model=model,
    tools=[consultar_runbook],
    system_prompt=SYSTEM_PROMPT,
)
```

O runtime do agente cuida do ciclo de tool calling. A aplicação apenas envia a pergunta e
consome a resposta final:

```python
resultado = agent.invoke({"messages": [("human", pergunta)]})
print(resultado["messages"][-1].text)
```

Quando a ferramenta é executada, ela imprime o parâmetro recebido. Esse log permite conferir
se o agente extraiu o identificador correto sem instrumentar todas as mensagens internas:

```text
Ferramenta: consultar_runbook(runbook_id='RB-381')
```

## Runbooks disponíveis

| ID | Serviço | Alerta | Cenário |
|---|---|---|---|
| `RB-274` | `catalog-api` | `OPS-4821` | Regressão após implantação |
| `RB-381` | `payments-worker` | `PAY-7712` | Falha após rotação de credencial |
| `RB-905` | `image-processor` | `MED-3304` | Pressão no volume temporário |

Todos seguem a mesma estrutura: identificação, objetivo, condição de uso, contexto,
sinais, pré-condições, procedimento em cinco etapas, critérios de sucesso, evidências,
escalonamento e restrições.

## Como rodar

```bash
cp .env.example .env      # preencha ANTHROPIC_API_KEY
uv sync

uv run agente-runbook-tool RB-274
uv run agente-runbook-tool RB-381
uv run agente-runbook-tool RB-905
```

Cada execução muda somente o ID interpolado na mesma pergunta. O ID impresso pela ferramenta
deve coincidir com o ID escolhido no comando, e a resposta deve conter as evidências e
restrições exclusivas daquele runbook.

## O que este exemplo não faz

- Não insere o conteúdo dos documentos no system prompt.
- Não abre nem instrumenta manualmente o ciclo de tool calling.
- Não entrega acesso livre ao filesystem.
- Não fragmenta nem indexa os documentos.
- Não usa embeddings, vector store ou recuperação seletiva.
- Não implementa RAG.

## Arquivos

```text
src/app.py                 configuração e uso do agente
src/tools.py               catálogo e ferramenta de consulta
dados/runbooks/RB-274.md   runbook da catalog-api
dados/runbooks/RB-381.md   runbook do payments-worker
dados/runbooks/RB-905.md   runbook do image-processor
.env.example               chave da API e modelo
pyproject.toml             dependências e comando `agente-runbook-tool`
```
