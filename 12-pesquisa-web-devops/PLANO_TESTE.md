# Plano de teste — ferramentas prontas

Roteiro manual para validar o exemplo antes da gravação. Rode tudo de dentro de
`12-pesquisa-web-devops`.

## 1. Instalação e estrutura

- [ ] `uv sync --locked` conclui sem alterar `uv.lock`.
- [ ] O comando instalado se chama `pesquisa-web-devops`.
- [ ] `.env`, `.venv` e caches estão ignorados (`git status` não os lista).
- [ ] `src/app.py` sai com `tools=[busca]`.
- [ ] Sem uma das três chaves, o comando para com a mensagem "Configure ... no arquivo .env".

## 2. O que o modelo recebe

- [ ] Convertidas com `convert_to_anthropic_tool` (de `langchain_anthropic.chat_models`), as
      ferramentas chegam como `tavily_search` e `firecrawl_scrape`.
- [ ] `tavily_search` exige só `query`; os demais argumentos (`include_domains`,
      `exclude_domains`, `search_depth`, `time_range`…) são opcionais e vêm descritos pelo
      pacote.
- [ ] `firecrawl_scrape` exige só `url`.

## 3. Busca

Com `tools=[busca]`:

```bash
uv run pesquisa-web-devops "Quais as tendências recentes de DevOps e cloud?"
```

- [ ] Ao menos uma linha `Ferramenta: tavily_search(...)` com a `query` escrita pelo modelo.
- [ ] A resposta cita fontes com URL.

## 4. Leitura

Troque para `tools=[leitura]`:

```bash
uv run pesquisa-web-devops "Resuma as novidades desta página: https://kubernetes.io/releases/"
```

- [ ] Uma linha `Ferramenta: firecrawl_scrape({'url': ...})` com a URL da pergunta.
- [ ] A resposta resume as versões listadas na página.
- [ ] Defina antes da gravação a URL das release notes mais recentes do Kubernetes, se preferir
      uma página mais específica que a de releases.

## 5. Camada gratuita

- [ ] O painel do Tavily e o do Firecrawl mostram o consumo de créditos das execuções acima.
- [ ] As páginas de preço abrem e mostram o plano gratuito sem cartão.

## 6. Fronteiras

- [ ] Uma ferramenta registrada por vez.
- [ ] Sem `@tool`, sem sobrescrever descrição, sem `try/except`, sem recorte do retorno.
- [ ] Sem `temperature`.
- [ ] Volte para `tools=[busca]` antes da gravação.

## Resultado observado

### Ferramentas invocadas direto, sem modelo (03/10/2026)

- `TavilySearch(max_results=5).invoke({"query": "tendências DevOps cloud 2026"})` devolveu as
  chaves `query`, `follow_up_questions`, `answer`, `images`, `results`, `response_time` e
  `request_id`, com 5 resultados (InfoQ, devops.com e outros). `answer` vem `None` sem
  `include_answer`.
- `FirecrawlScrape().invoke({"url": "https://kubernetes.io/releases/"})` devolveu um dict com
  `markdown` (~8,3 mil caracteres, versões 1.37, 1.36 e 1.35 em manutenção) e `metadata`.

### Pelo agente (03/10/2026, `claude-sonnet-5`)

| Demo | Linhas `Ferramenta:` | Resposta | Tempo |
|---|---|---|---|
| Busca, "Quais as tendências recentes de DevOps e cloud?" | 3 × `tavily_search`, com `query` em português e inglês, `search_depth='advanced'` e `topic='general'` escolhidos pelo modelo | Tendências em DevOps e cloud, com 6 fontes com URL | ~24 s |
| Leitura, "Resuma as novidades desta página: https://kubernetes.io/releases/" | 1 × `firecrawl_scrape({'url': 'https://kubernetes.io/releases/'})` | Versões 1.37, 1.36 e 1.35 suportadas, datas de EOL e a 1.38 em planejamento | ~12 s |

Dois pontos a observar na gravação:

- O modelo preenche argumentos opcionais do esquema do pacote por conta própria:
  `search_depth='advanced'` consome mais créditos que o padrão `basic`.
- O modelo não sabe a data de hoje: escreveu "2025" nas queries de tendências e, na leitura,
  comentou que a página parecia "futura" em relação a 2025.
