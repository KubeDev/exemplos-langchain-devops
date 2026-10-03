# 12 — Ferramentas prontas: busca e leitura

Nos exemplos `09` a `11`, toda ferramenta foi escrita à mão: a função, a docstring, o esquema.
Este exemplo faz o contrário. As duas ferramentas vêm prontas de pacotes de integração do
ecossistema LangChain, e o agente pesquisa sobre DevOps e cloud na web sem uma linha de
ferramenta escrita aqui.

O ponto da aula é este: **nem toda ferramenta precisa ser escrita**. Uma ferramenta pronta entra
no agente com um pacote, uma chave e uma linha, e as duas deste exemplo têm camada gratuita.

## As duas ferramentas

| Ferramenta | Pacote | Classe | O que faz | Retorno |
|---|---|---|---|---|
| `busca` | `langchain-tavily` | `TavilySearch` | Pesquisa na web | Lista de resultados com título, URL e conteúdo |
| `leitura` | `langchain-firecrawl` | `FirecrawlScrape` | Lê uma página a partir da URL | O conteúdo da página em markdown, com metadados |

Cada pacote traz mais de uma ferramenta: o `langchain-firecrawl` tem `FirecrawlScrape`,
`FirecrawlCrawl`, `FirecrawlMap`, `FirecrawlExtract` e `FirecrawlSearch`. O exemplo registra só a
que precisa.

## O agente

`src/app.py` importa e instancia as duas ferramentas. A que o agente usa é escolhida por **uma
linha**:

```python
# Troque a ferramenta: busca · leitura
tools=[busca],
```

Fica uma ferramenta registrada por vez. Trocar de fornecedor, ou de capacidade, é trocar essa
linha.

Como a ferramenta pronta não tem um corpo nosso onde colocar um `print`, o `app.py` lê a chamada
pedida pelo modelo nas mensagens do resultado e imprime a mesma linha dos exemplos anteriores:

```text
Ferramenta: tavily_search({'query': 'tendências DevOps cloud 2026'})
```

## Chaves e camada gratuita

Além da `ANTHROPIC_API_KEY`, cada ferramenta pede a chave do seu serviço:

- `TAVILY_API_KEY`, criada em <https://app.tavily.com>
- `FIRECRAWL_API_KEY`, criada em <https://www.firecrawl.dev/app/api-keys>

As duas têm camada gratuita com créditos mensais e não pedem cartão. Os limites mudam com o
tempo: confira nas páginas de preço do [Tavily](https://www.tavily.com/pricing) e do
[Firecrawl](https://www.firecrawl.dev/pricing).

## Como rodar

```bash
cp .env.example .env      # preencha as três chaves
uv sync

# com tools=[busca]
uv run pesquisa-web-devops "Quais as tendências recentes de DevOps e cloud?"

# com tools=[leitura]
uv run pesquisa-web-devops "Resuma as novidades desta página: https://kubernetes.io/releases/"
```

## O que este exemplo não faz

- Não registra as duas ferramentas juntas: busca e leitura não se encadeiam aqui.
- Não compara fornecedores nem avalia a ferramenta pronta.
- Não escreve ferramenta própria nem altera a descrição das ferramentas prontas.
- Não trata erro nem recorta o retorno: o modelo recebe o que a ferramenta devolve.

## Arquivos

```text
src/app.py        agente; uma linha escolhe a ferramenta pronta
.env.example      chaves da Anthropic, do Tavily e do Firecrawl, e o modelo
PLANO_TESTE.md    validação manual e critérios de aceite da demo
pyproject.toml    dependências e comando `pesquisa-web-devops`
```
