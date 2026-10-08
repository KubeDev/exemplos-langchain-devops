# Contexto para sessões de IA neste projeto

Leia o `README.md` antes de alterar este exemplo. Ele registra a demonstração e suas fronteiras.

## Natureza do projeto

Exemplo didático `14` da série `langchain-devops-examples`. A lição é: **o retorno de uma
ferramenta publicada declara o escopo em que foi produzido**, porque o consumidor é desconhecido;
sem isso, vazio ou parcial sem erro vira falha silenciosa.

O exemplo é autocontido e parte de uma cópia do `13` (código duplicado, nada compartilhado).
Quando simplicidade e robustez colidirem, vence a simplicidade.

## Server

- Todo o server fica em `src/servidor.py`, com FastMCP e `@mcp.tool`. As quatro ferramentas do
  `13` continuam, todas de leitura.
- A alternância da demo é a troca do import de `retornar` (`src/retornos/sem_escopo.py` ×
  `src/retornos/com_escopo.py`), no mesmo estilo do `11`. O recorte é idêntico nas duas versões;
  só o retorno muda. Não transforme isso em variável de ambiente nem em flag.
- O estado versionado começa em `sem_escopo`, para a demo abrir pela falha.
- O escopo vai no **texto** (`content`). O `structured_content` é complementar: no cliente
  LangChain ele vira artefato e não chega ao modelo.
- `AGORA_DADOS` congela o relógio dos dados fictícios; `PERIODO_PADRAO_HORAS` fica fora do
  esquema de propósito (é o caso de quebra silenciosa da aula).
- A falha silenciosa da demo é `CH-1043` × `MUD-305` (03/10), fora das últimas 24 horas. Não mova
  as datas de `dados/` sem conferir os testes.
- `listar_droplets` filtra por `regiao` (como `nyc1`) na aplicação, como o `13`; por isso pagina
  localmente: busca, filtra e só então corta com `pagina`/`limite`, declarando o total filtrado.
  Lê `DIGITALOCEAN_TOKEN` dentro da função. `consultar_chamado` não declara escopo: é consulta por identificador.
- A versão do contrato é `FastMCP("operacao", version=...)`. Não construa mecanismo de
  versionamento nem de depreciação: compatível × quebra fica no comentário e no README.
- Transporte stdio: nada de `print` no stdout dentro do server.

## Clientes

- `src/agente.py` é o mesmo do `13`. Preserve `input()`, uma pergunta por execução e
  `agent.ainvoke()` sem streaming. `MCP_CONFIG` e `.mcp.json` continuam iguais.

## Testes

`tests/test_servidor.py` usa o cliente em memória do FastMCP, sem modelo. A fixture
`retorno_com_escopo` faz a troca de módulo com `monkeypatch`. O teste de `listar_droplets` é
pulado sem `DIGITALOCEAN_TOKEN`.

## Fronteiras curriculares

- Não adicione ferramenta de escrita nem amplie o escopo do token: é o exemplo `15`.
- Não suba o server por HTTP nem faça deploy.
- Não adicione autenticação, middleware, retry, cache, memória ou streaming.
- Não pagine a listagem de ferramentas do protocolo.

## Ambiente e credenciais

- Use somente `uv`; dependências por `uv add` e `uv remove`.
- Não use `temperature`, `top_p` ou `top_k`.
- `ANTHROPIC_API_KEY` e `DIGITALOCEAN_TOKEN` nunca entram em arquivo versionado.
- O token do DigitalOcean tem escopo customizado `droplet:read`.
