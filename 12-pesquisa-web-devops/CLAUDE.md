# Contexto para sessões de IA neste projeto

Leia o `README.md` para entender a demonstração. Este arquivo registra as fronteiras que
preservam a função didática do exemplo.

## Natureza do projeto

Exemplo didático `12` da série `langchain-devops-examples`. A lição é: **existe ferramenta
pronta, ela entra no agente com um pacote, uma chave e uma linha, e tem camada gratuita**.

O código será lido em aula e projetado numa tela. Quando simplicidade e robustez colidirem,
vence a simplicidade.

## A troca de ferramenta é o experimento

- `src/app.py` importa e instancia as duas ferramentas (`busca` e `leitura`). A escolha é a
  linha `tools=[...]` do `create_agent`. Não troque esse mecanismo por variável de ambiente,
  argumento de CLI ou flag: a troca tem que ser visível no código.
- O `app.py` sai com `tools=[busca]`, o ponto de partida da demo.
- **Uma ferramenta registrada por vez.** Não registre as duas juntas: o encadeamento
  busca → leitura e a colisão entre pacotes não são assunto desta aula.
- A linha `Ferramenta: ...` é lida dos `tool_calls` das mensagens do resultado, porque a
  ferramenta pronta não tem corpo nosso para o `print`. Mantenha o formato dos exemplos `09` a
  `11`.

## Fronteiras curriculares

- Não escreva ferramenta própria nem envolva as ferramentas prontas num `@tool`.
- Não sobrescreva `name`, `description` nem esquema das ferramentas prontas.
- Não configure parâmetros além de `max_results` no `TavilySearch`; o `FirecrawlScrape` fica
  sem argumentos.
- Não adicione `try/except`, contrato de retorno, retry, cache, recorte do retorno nem
  middleware.
- Não adicione avaliação nem comparação entre fornecedores.

## Ambiente e pacotes

- Use somente `uv`; nunca `pip`, Poetry, Conda ou ativação manual de virtualenv.
- Dependências devem ser alteradas com `uv add` ou `uv remove` para preservar o lockfile.
- Não use `temperature`, `top_p` ou `top_k`.

## Credenciais

`ANTHROPIC_API_KEY`, `TAVILY_API_KEY` e `FIRECRAWL_API_KEY` nunca entram no repositório.
`.env.example` contém somente placeholders e `.env` permanece ignorado. Não fixe números de
camada gratuita nos arquivos: aponte para as páginas de preço.
