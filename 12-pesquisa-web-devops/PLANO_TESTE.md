# Plano de teste — ferramenta pronta

Roteiro manual para validar o exemplo antes da gravação. Rode tudo de dentro de
`12-pesquisa-web-devops`.

## 1. Instalação e estrutura

- [ ] `uv sync --locked` conclui sem alterar `uv.lock`.
- [ ] O comando instalado se chama `pesquisa-web-devops`.
- [ ] `.env`, `.venv` e caches estão ignorados (`git status` não os lista).
- [ ] `src/app.py` registra `tools=[busca]`.
- [ ] Sem uma das duas chaves, o comando para com a mensagem "Configure ... no arquivo .env".

## 2. O que o modelo recebe

- [ ] O comando da seção "O esquema que o modelo recebe" do README imprime o esquema sem chamar
      API.
- [ ] A ferramenta chega como `tavily_search` e exige só `query`; os demais argumentos
      (`include_domains`, `exclude_domains`, `search_depth`, `time_range`…) são opcionais e vêm
      descritos pelo pacote.

## 3. Busca

```bash
uv run pesquisa-web-devops "Quais as tendências recentes de DevOps e cloud?"
```

- [ ] Ao menos uma linha `Ferramenta: tavily_search(...)` com a `query` escrita pelo modelo: é o
      que sai do ambiente para o Tavily.
- [ ] A resposta cita fontes com URL.
- [ ] O painel do Tavily mostra o consumo das execuções acima.

## 4. Fronteiras

- [ ] Uma única ferramenta registrada.
- [ ] Sem `@tool`, sem sobrescrever descrição, sem `try/except`, sem recorte do retorno.
- [ ] Sem `temperature`.

## Resultado observado

### Ferramenta invocada direto, sem modelo (03/10/2026)

- `TavilySearch(max_results=5).invoke({"query": "tendências DevOps cloud 2026"})` devolveu as
  chaves `query`, `follow_up_questions`, `answer`, `images`, `results`, `response_time` e
  `request_id`, com 5 resultados (InfoQ, devops.com e outros). `answer` vem `None` sem
  `include_answer`.

### Pelo agente (03/10/2026, `claude-sonnet-5`)

| Demo | Linhas `Ferramenta:` | Resposta | Tempo |
|---|---|---|---|
| "Quais as tendências recentes de DevOps e cloud?" | 3 × `tavily_search`, com `query` em português e inglês, `search_depth='advanced'` e `topic='general'` escolhidos pelo modelo | Tendências em DevOps e cloud, com 6 fontes com URL | ~24 s |

Dois pontos a observar na gravação:

- O modelo preenche argumentos opcionais do esquema do pacote por conta própria:
  `search_depth='advanced'` consome mais que o padrão `basic`.
- O modelo não sabe a data de hoje: escreveu "2025" nas queries de tendências.
