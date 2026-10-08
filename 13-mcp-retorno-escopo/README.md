# 14 — Retorno com escopo declarado

Este exemplo independente parte do server de operação do `12` e muda uma coisa: o **retorno** das
ferramentas. O server publicado é lido por agentes que o autor não conhece, e esses agentes não
têm como saber em que recorte o resultado foi produzido.

O ponto da aula é este: **retorno vazio ou parcial sem erro não é resposta**. Se o server aplica
um filtro, um período padrão ou um limite de página e não conta isso no retorno, o consumidor
transforma o recorte em conclusão. É a falha silenciosa: sucesso aparente, conclusão falsa,
confiança alta.

## A falha silenciosa

`consultar_historico_mudancas` consulta, quando o consumidor não informa `horas`, só as últimas
24 horas. O valor padrão é aplicado dentro do server e não aparece no esquema:

```python
PERIODO_PADRAO_HORAS = 24

horas = horas or PERIODO_PADRAO_HORAS
desde = AGORA_DADOS - timedelta(hours=horas)
```

O chamado `CH-1043` (fila de pedidos acumulando mensagens, aberto em 06/10 às 16h10) tem uma
causa provável no histórico: a `MUD-305`, atualização da biblioteca do consumidor de mensagens,
executada em 03/10. Ela existe, mas fica fora das últimas 24 horas.

Os dados de `dados/` são fictícios e congelados: as consultas a eles partem de `AGORA_DADOS`
(06/10/2026, 16h30), para a demonstração dar o mesmo resultado em qualquer dia.

## As duas versões do retorno

O recorte é o mesmo nas duas versões; muda só o que o retorno conta. A troca é uma linha no
topo de `src/servidor.py`:

```python
# Troque o módulo para mudar o retorno das ferramentas:
# sem_escopo · com_escopo
from src.retornos.sem_escopo import retornar
```

`src/retornos/sem_escopo.py` devolve só os itens. O server sabe o escopo e não conta:

```text
[]
```

`src/retornos/com_escopo.py` põe o escopo no texto, antes do resultado:

```text
Escopo da consulta
filtro: servico=fila-pedidos
periodo: últimas 24 horas, de 2026-10-05T16:30:00-03:00 até 2026-10-06T16:30:00-03:00
valor_padrao_aplicado: horas=24
retornados: 0 (todas as mudanças do período)
fora_do_escopo: mudanças anteriores ao período não foram consultadas; informe horas para ampliar
consultado_em: 2026-10-06T16:30:00-03:00

Resultado
[]
```

### Conteúdo e conteúdo estruturado

A versão com escopo devolve um `ToolResult` com as duas partes do resultado MCP:

```python
return ToolResult(content=texto, structured_content={"escopo": escopo, "itens": itens})
```

- `content` é o texto que o modelo lê;
- `structured_content` é para clientes que leem dados.

No cliente LangChain (`MCPAdapter`), o `content` vira o conteúdo da `ToolMessage` e o
`structured_content` vira o **artefato**, que não chega ao modelo. Escopo só no estruturado não
resolve: ele tem de estar no texto.

## O mesmo princípio nas outras ferramentas

| Ferramenta | O que o retorno passa a declarar |
|---|---|
| `consultar_historico_mudancas` | filtro, período, valor padrão aplicado, retornados, o que ficou fora, momento da consulta |
| `buscar_runbook` | filtro, regra de comparação, retornados de quantos runbooks do catálogo |
| `listar_droplets` | filtro, nível de detalhe, página, retornados de quantos no total, próxima página, momento da consulta |
| `consultar_chamado` | nada: consulta por identificador, e o "não encontrado" já é explícito |

`listar_droplets` mantém o filtro opcional por `regiao` (como `nyc1`) e ganha três parâmetros
opcionais:

- `detalhe`: `resumido` (padrão) traz só o nome legível, o status e a região; `completo` traz os
  campos principais, os mesmos do `09` e do `12` (`id`, `nome`, `status`, `regiao`, `tamanho`,
  `vcpus`, `memoria_mb`, `disco_gb`, `ip_publico`, `tags`, `criado_em`), nunca o objeto inteiro da API;
- `pagina` e `limite`: como o filtro por região é feito no server, a página também é: ele busca os
  Droplets, filtra pela região e só então corta a página, declarando o filtro, `retornados: N de T`
  sobre o total filtrado e `proxima_pagina`.

Com o laboratório do `09` na conta (`web-01` e `worker-01` em `nyc1`, `batch-01` em `sfo3`),
`regiao=nyc1` com `limite=1` retorna `filtro: regiao=nyc1`, `retornados: 1 de 2` e
`proxima_pagina: 2`; sem região, o filtro aparece como `todas as regiões`.

No resumo, o identificador é legível: `web-01 (501234567)`, nome junto do ID.

## Descrição e retorno como contrato

Descrição, esquema e retorno formam o contrato público do server. O autor não controla os
consumidores, então mudar qualquer um dos três muda o comportamento de agentes que ele nunca
viu. A versão vai no `serverInfo`:

```python
mcp = FastMCP("operacao", version="1.0.0")
```

| Mudança | Classificação |
|---|---|
| parâmetro opcional novo (`detalhe`, `pagina`, `limite`, `horas`) | compatível |
| campo novo no retorno | compatível |
| renomear ou remover ferramenta, parâmetro ou campo | quebra |
| tornar um parâmetro obrigatório | quebra |
| trocar um valor padrão, como `PERIODO_PADRAO_HORAS` | quebra silenciosa |
| reescrever uma descrição | muda a escolha de quem consome |

A troca do valor padrão é o caso que mais engana: `PERIODO_PADRAO_HORAS` fica fora do esquema
(`horas` tem padrão `null`), então trocar 24 por 1 não muda nada que um teste de esquema
compare, e muda o que todo consumidor recebe: a `MUD-311` (15h25) sai da última hora antes das
16h30 e a pergunta do `CH-1042` passa a voltar vazia. Com a troca, `test_periodo_padrao_fora_do_esquema`
continua verde; ficam vermelhos só os testes de comportamento,
`test_periodo_padrao_alcanca_a_mudanca_da_tarde` e `test_com_escopo_o_vazio_declara_o_recorte`.

Ao aposentar uma ferramenta publicada, o aviso vai nos dois lugares que o consumidor lê: na
descrição, indicando a sucessora, e no retorno, com a data de remoção. A remoção só acontece
depois da janela anunciada, numa versão major.

## Como executar

```bash
cp .env.example .env
uv sync
uv run agente-operacao
```

Pergunta sugerida para a demonstração:

```text
O chamado CH-1043 está aberto. Houve alguma mudança recente na fila-pedidos que possa ter
causado o problema?
```

1. Com `sem_escopo`: o server registra `consultar_historico_mudancas(servico='fila-pedidos', horas=None)`,
   recebe `[]`, e o agente responde que não houve mudança.
2. Troque o import para `com_escopo` e repita a pergunta: a resposta cita o período consultado e
   o agente amplia a busca com `horas`, chegando à `MUD-305`.

O Claude Code usa o mesmo `.mcp.json` do `12`; abra-o nesta pasta e faça a mesma pergunta.

## Verificação

### Suíte de testes

`tests/test_servidor.py` testa o server pelo cliente MCP em memória do FastMCP, sem modelo. A
fixture `retorno_com_escopo` faz a mesma troca de módulo durante o teste:

```python
monkeypatch.setattr(servidor, "retornar", com_escopo.retornar)
```

```bash
uv run pytest
```

Os testes de dados locais rodam offline e cobrem o escopo declarado: o vazio sem escopo, o vazio
com o recorte declarado, a ampliação do período, o escopo presente no texto, o padrão fora do
esquema e a versão no `serverInfo`. O teste de `listar_droplets` com página e total só roda com
`DIGITALOCEAN_TOKEN`; sem ele, aparece como `skipped`.

### MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv run servidor-operacao
```

Chame `consultar_historico_mudancas` com `servico=fila-pedidos`, sem `horas`, e compare as abas
de conteúdo e de conteúdo estruturado nas duas versões.

## Pré-requisitos

- Python 3.12 e `uv`;
- chave da API da Anthropic;
- token do DigitalOcean com escopo customizado `droplet:read`;
- Node.js e `npx`, só para o Inspector;
- Claude Code, só para o segundo cliente.

## O que este exemplo não faz

- Não escreve nem altera recursos: todas as ferramentas são de leitura.
- Não implementa mecanismo de versionamento nem de depreciação: a versão é um campo do `serverInfo`.
- Não pagina a listagem de ferramentas do protocolo: a paginação é do resultado de `listar_droplets`.
- Não sobe o server por HTTP, não adiciona autenticação, middleware, retry ou cache.

## Arquivos

```text
src/servidor.py              MCP server: recortes, escopo de cada ferramenta e versão do contrato
src/retornos/sem_escopo.py   retorno só com os itens
src/retornos/com_escopo.py   retorno com o escopo no texto e o conteúdo estruturado ao lado
src/agente.py                cliente LangChain, igual ao do 12
dados/                       chamados, runbooks e histórico de mudanças fictícios
tests/test_servidor.py       escopo declarado testado pelo cliente MCP em memória
.mcp.json                    o mesmo server registrado para o Claude Code
.env.example                 chave da API, modelo e token do DigitalOcean
PLANO_TESTE.md               validação manual da demonstração
pyproject.toml               dependências e comandos `servidor-operacao` e `agente-operacao`
```
