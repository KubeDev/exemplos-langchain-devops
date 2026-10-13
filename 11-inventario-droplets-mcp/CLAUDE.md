# Contexto para sessões de IA neste projeto

Leia o `README.md` para entender a demonstração. Este arquivo registra as fronteiras que
preservam a função didática do exemplo.

## Natureza do projeto

Exemplo didático `11` da série `langchain-devops-examples`. A lição é: **o agente não declara
ferramenta; descobre o catálogo inteiro de um MCP server próprio (DigitalOcean)**, inclusive
ferramentas de escrita.

O código será lido em aula e projetado numa tela. Quando simplicidade e robustez colidirem,
vence a simplicidade.

## Fronteiras

- Todo o código do agente fica em `src/app.py`. Não volte a ter ferramenta local,
  `src/droplets.py` nem `src/ferramentas/`: isso é o `09`.
- O agente registra **todas** as ferramentas que `adapter.list_tools()` devolver. Não filtre,
  não renomeie e não embrulhe ferramentas no cliente.
- O server (`MCP_URL`, padrão `http://localhost:8000/mcp`) é do autor e fica fora deste
  repositório. O token da DigitalOcean do agente mora no server; o cliente não lê
  `DIGITALOCEAN_TOKEN`.
- O único freio das ferramentas de escrita é o system prompt. Não adicione confirmação humana
  (HITL), middleware, autenticação no MCP, retry, cache ou tratamento abrangente de erro.
- Não ative `strict` no provider.
- Os scripts de `setup/` são preparação de cenário, não parte da lição. Usam
  `DIGITALOCEAN_TOKEN_SETUP` e só tocam em Droplets com a tag `inventario-droplets`. Mudou a
  tabela do `setup/criar_droplets.py`, atualize a do README.

## Ambiente e pacotes

- Use somente `uv`; nunca `pip`, Poetry, Conda ou ativação manual de virtualenv.
- Dependências devem ser alteradas com `uv add` ou `uv remove` para preservar o lockfile.
- Não use `temperature`, `top_p` ou `top_k`.

## Credenciais

`ANTHROPIC_API_KEY` e `DIGITALOCEAN_TOKEN_SETUP` nunca entram no repositório. `.env.example`
contém somente placeholders e `.env` permanece ignorado. Não grave id de conta, nome de time
ou id de Droplet real em nenhum arquivo versionado.
