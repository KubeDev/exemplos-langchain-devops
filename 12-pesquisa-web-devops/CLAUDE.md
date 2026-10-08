# Contexto para sessões de IA neste projeto

Leia o `README.md` para entender a demonstração. Este arquivo registra as fronteiras que
preservam a função didática do exemplo.

## Natureza do projeto

Exemplo didático `12` da série `langchain-devops-examples`. A lição é: **existe ferramenta
pronta, ela entra no agente com um pacote e uma chave; o esquema enviado ao modelo é do pacote,
e a consulta sai do seu ambiente para um terceiro (o Tavily)**.

O código será lido em aula e projetado numa tela. Quando simplicidade e robustez colidirem,
vence a simplicidade.

## O agente

- `src/app.py` registra uma única ferramenta pronta, `busca` (`TavilySearch`), em `tools=[busca]`.
- Não acrescente outra ferramenta, outro fornecedor nem mecanismo de troca.
- A linha `Ferramenta: ...` é lida dos `tool_calls` das mensagens do resultado, porque a
  ferramenta pronta não tem corpo nosso para o `print`. Ela mostra os argumentos que vão para o
  Tavily. Mantenha o formato dos exemplos `09` a `11`.

## Fronteiras curriculares

- Não escreva ferramenta própria nem envolva a ferramenta pronta num `@tool`.
- Não sobrescreva `name`, `description` nem esquema da ferramenta pronta.
- Não configure parâmetros além de `max_results` no `TavilySearch`.
- Não adicione `try/except`, contrato de retorno, retry, cache, recorte do retorno nem
  middleware.
- Não adicione comparação entre fornecedores.

## Ambiente e pacotes

- Use somente `uv`; nunca `pip`, Poetry, Conda ou ativação manual de virtualenv.
- Dependências devem ser alteradas com `uv add` ou `uv remove` para preservar o lockfile.
- Não use `temperature`, `top_p` ou `top_k`.

## Credenciais

`ANTHROPIC_API_KEY` e `TAVILY_API_KEY` nunca entram no repositório. `.env.example` contém
somente placeholders e `.env` permanece ignorado. Não fixe números de plano, créditos ou preço
nos arquivos: aponte para a página de preços.
