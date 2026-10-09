# 10 · Ferramenta pronta: busca na web com Tavily

No exemplo `09`, a ferramenta foi escrita à mão: a função, a docstring, o esquema.
Este exemplo faz o contrário. A ferramenta vem pronta de um pacote de integração do ecossistema
LangChain, e o agente pesquisa sobre DevOps e cloud na web sem uma linha de ferramenta escrita
aqui.

O ponto da aula: **nem toda ferramenta precisa ser escrita**. Uma ferramenta pronta entra no
agente com um pacote e uma chave. Em troca, o esquema que o modelo recebe é do pacote, e a
consulta sai do seu ambiente para um terceiro.

## A ferramenta

| Ferramenta | Pacote | Classe | O que faz | Retorno |
|---|---|---|---|---|
| `busca` | `langchain-tavily` | `TavilySearch` | Pesquisa na web | Lista de resultados com título, URL e conteúdo |

```python
busca = TavilySearch(max_results=5)

agent = create_agent(model=model, tools=[busca], system_prompt=SYSTEM_PROMPT)
```

## O esquema que o modelo recebe

O nome, a descrição e os argumentos vêm do pacote. Para ver exatamente o que é enviado ao
modelo, sem chamar nenhuma API:

```bash
TAVILY_API_KEY=x uv run python -c "
import json
from langchain_tavily import TavilySearch
from langchain_anthropic.chat_models import convert_to_anthropic_tool
print(json.dumps(convert_to_anthropic_tool(TavilySearch(max_results=5)), indent=2, ensure_ascii=False))"
```

A ferramenta chega ao modelo como `tavily_search`. Só `query` é obrigatório; `include_domains`,
`exclude_domains`, `search_depth`, `time_range`, `topic` e os demais são opcionais, e o modelo
pode preenchê-los por conta própria.

## O que sai do seu ambiente

Como a ferramenta pronta não tem um corpo nosso onde colocar um `print`, o `app.py` lê a chamada
pedida pelo modelo nas mensagens do resultado:

```text
Ferramenta: tavily_search({'query': 'tendências DevOps cloud 2026'})
```

Esses argumentos são o que vai para o Tavily: a consulta, escrita pelo modelo a partir da sua
pergunta, deixa o seu ambiente e chega a um serviço de terceiro. Antes de usar uma ferramenta
pronta, vale perguntar que dado ela envia e para quem.

## Chaves

Além da `ANTHROPIC_API_KEY`, a ferramenta pede a `TAVILY_API_KEY`, criada em
<https://app.tavily.com>. Planos e limites mudam com o tempo: confira na
[página de preços do Tavily](https://www.tavily.com/pricing).

## Como rodar

```bash
cp .env.example .env      # preencha as duas chaves
uv sync
uv run pesquisa-web-devops "Quais as tendências recentes de DevOps e cloud?"
```

## O que este exemplo não faz

- Não escreve ferramenta própria nem altera a descrição da ferramenta pronta.
- Não compara fornecedores.
- Não trata erro nem recorta o retorno: o modelo recebe o que a ferramenta devolve.

## Arquivos

```text
src/app.py        agente com a ferramenta pronta de busca
.env.example      chaves da Anthropic e do Tavily, e o modelo
pyproject.toml    dependências e comando `pesquisa-web-devops`
```
