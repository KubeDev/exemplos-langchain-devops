# 15 — Escrita controlada

Este exemplo independente parte do server de operação do `14`, já com o escopo declarado no
retorno, e muda uma coisa: o server ganha **uma ferramenta de escrita**, `desligar_droplet`.

O ponto da aula é este: **a escrita entra recortada**. O token com `droplet:update` permite
muito mais do que desligar um Droplet; quem decide o que é publicado é o server, não o token.
Ele publica uma ação nomeada e estreita, com parâmetro restrito, efeito declarado no retorno e o
registro do que ficou de fora.

## O token permite mais do que o server publica

O escopo customizado do DigitalOcean é por tipo de recurso, não por Droplet. Com
`droplet:update`, o token libera, em **todos** os Droplets da conta, as Droplet actions
`shutdown`, `power_off`, `power_on`, `reboot`, `power_cycle`, `rename`, `enable_backups`,
`disable_backups`, entre outras (a lista completa está na documentação das Droplet Actions).

O server recorta isso em uma ação, sobre três Droplets:

| Camada | O que permite |
|---|---|
| Escopo do token | toda Droplet action de `droplet:update`, em qualquer Droplet da conta |
| Escopo do server | só `shutdown`, só em `web-01`, `worker-01` e `batch-01` com a tag `inventario-droplets` |
| Escopo do agente | as ferramentas que o cliente entrega ao modelo, que podem ser menos do que o server publica |

O escopo do agente é decidido no cliente. Um agente só de consulta poderia receber o catálogo
sem a ferramenta de escrita; este exemplo não faz isso, para a demonstração mostrar a escrita:

```python
tools = [tool for tool in await adapter.list_tools() if tool.name != "desligar_droplet"]
```

## Assimetria entre leitura e escrita

São dois tokens, lidos pelo server em ferramentas diferentes:

| Variável | Escopo | Usada por |
|---|---|---|
| `DIGITALOCEAN_TOKEN` | `droplet:read` | `listar_droplets` |
| `DIGITALOCEAN_TOKEN_ESCRITA` | `droplet:read` e `droplet:update` | `desligar_droplet` |

A leitura continua ampla (qualquer região, paginada) e com o token que não altera nada. A escrita é
estreita e é a única que encosta no token ampliado. Se a ferramenta de escrita for removida, o
token de escrita sai junto; a leitura não muda.

O `droplet:read` no token de escrita existe porque a ferramenta precisa achar o Droplet pela tag
antes de agir.

## A ferramenta de escrita

```python
TAG_LABORATORIO = "inventario-droplets"
DROPLETS_PERMITIDOS = Literal["web-01", "worker-01", "batch-01"]

@mcp.tool(annotations=ESCRITA)
def desligar_droplet(droplet: Annotated[DROPLETS_PERMITIDOS, Field(...)]) -> ToolResult:
```

### Parâmetro restrito

O recorte tem duas camadas, e as duas acontecem antes de qualquer action:

1. **No esquema**: `droplet` é um `enum` com os três nomes do laboratório. O consumidor vê os
   valores permitidos, e um pedido como `db-producao` é recusado pela validação do server, antes
   de a função rodar.
2. **Na função**: o nome não basta. A ferramenta busca os Droplets com a tag
   `inventario-droplets` e só age sobre o que tiver o nome pedido **e** a tag. Um `worker-01` fora
   do laboratório é recusado com um erro acionável, que diz o que fazer:

```text
worker-01 não tem a tag inventario-droplets nesta conta; nada foi feito. Use listar_droplets para
ver os Droplets e as tags de cada um.
```

A tag não é filtro do usuário, como a `regiao` de `listar_droplets`: é o recorte de segurança do
laboratório, fixo no server.

Nome de Droplet não é único no DigitalOcean. O laboratório tem um Droplet por nome, mas a
ferramenta se protege do caso contrário: se um dia houver dois `web-01` com a tag, ela não escolhe
um por conta própria; recusa, lista os IDs e pede que os duplicados sejam resolvidos.

Os Droplets do laboratório são os criados pelos scripts de `setup/` do `09`: `web-01` e `worker-01`
em `nyc1`, ativos, e `batch-01` em `sfo3`, desligado de propósito; um Droplet por nome. A escrita
não olha a região: o recorte é nome e tag.

### Efeito declarado no retorno

O retorno não diz só "ok": declara o que foi pedido, o estado anterior, a action disparada, o que
não foi feito e como compensar.

```text
Efeito da ação
pedido: shutdown gracioso de web-01 (501234567)
estado_anterior: active
acao_disparada: shutdown, action 2345678901, status in-progress, iniciada em 2026-10-06T19:30:00Z
garantia: o comando foi emitido, não confirmado; consulte o status com listar_droplets
nao_feito: nenhum power_off, reboot ou destroy; nenhum outro Droplet foi tocado
compensacao: religar com a action power_on, fora deste server; a indisponibilidade já aconteceu
```

Se o Droplet já estava `off`, como o `batch-01` do laboratório, nenhuma action é disparada e o
retorno diz isso: pedir de novo não
produz efeito novo.

### Compensável, não reversível

Na matriz da Aula 01, `shutdown` é escrita **compensável**: religar com `power_on` traz o Droplet
de volta, mas a indisponibilidade já aconteceu e não se desfaz. Por isso o retorno nomeia a
compensação e diz o que ela não recupera.

### Anotações de ferramenta

As ferramentas de leitura são publicadas com `readOnlyHint: true`; `desligar_droplet`, com
`readOnlyHint: false` e `destructiveHint: true`. São **dicas ao cliente**: um cliente pode usá-las
para pedir confirmação antes de chamar a ferramenta, mas o server não tem como exigir isso.

## O que ficou de fora e por quê

| Ação | Por que não é publicada |
|---|---|
| `power_off` | corte de energia: o próprio DigitalOcean recomenda usá-lo só quando o `shutdown` falha, porque pode causar complicações no sistema |
| `power_on` | é a compensação; fica com quem opera, para o agente não religar o que alguém desligou de propósito |
| `reboot`, `power_cycle` | outra intenção (reiniciar), com outro blast radius; entraria como outra ferramenta nomeada |
| `resize`, `rebuild`, `restore`, `snapshot`, `rename` | mudam o Droplet em si, não só o estado de energia; algumas pedem escopos além de `droplet:update` |
| destruir o Droplet | irreversível; o token deste exemplo nem tem `droplet:delete` |
| ação genérica (`executar_acao(tipo)`) | publicaria o escopo inteiro do token com outro nome |

**Por que `shutdown` antes de `power_off`:** o `shutdown` pede ao sistema operacional que desligue
de forma limpa, como o comando `shutdown` no console: serviços param, discos são sincronizados. O
`power_off` é tirar da tomada. A documentação do DigitalOcean recomenda tentar o `shutdown` e só
recorrer ao `power_off` se ele falhar. O `shutdown` garante que o comando foi emitido, não que o
desligamento terminou; por isso o retorno diz "não confirmado".

## A fronteira do protocolo

O MCP padroniza a **descoberta** (`tools/list`), a **chamada** (`tools/call`), o **esquema** de
entrada e o **formato do resultado**. No transporte HTTP, a especificação prevê autenticação: quem
está conectando.

O que o protocolo não traz, e este server também não implementa:

- **autorização por ação**: se este agente pode desligar este Droplet agora;
- **auditoria**: quem pediu, quando, com que resultado;
- **validação de conteúdo**: se o pedido faz sentido no contexto da operação.

Isso fica com a aplicação. O server deste exemplo não tem gate, aprovação humana nem trilha, e
isso é decisão declarada: essa lacuna fica fora deste exemplo.

## Como executar

```bash
cp .env.example .env
uv sync
uv run agente-operacao
```

Pedidos sugeridos, na ordem da demonstração (uma execução por pedido):

```text
Desligue o Droplet web-01 do laboratório.
```

```text
Desligue o Droplet db-producao.
```

```text
Force o desligamento do web-01 com power_off.
```

1. O server registra `desligar_droplet(droplet='web-01')` e o agente responde com o efeito
   declarado: estado anterior, action disparada e como religar.
2. `db-producao` está fora do `enum`: o pedido é recusado pelo server.
3. Não existe ferramenta de `power_off` nem de destruir: o agente não tem o que chamar, mesmo com
   o token permitindo.

O Claude Code usa o `.mcp.json` desta pasta, com a mesma entrada `operacao`; o server lê os dois tokens do `.env` (`load_dotenv()`). Abra-o nesta pasta e faça os mesmos pedidos.

### Religar depois da demonstração

O `power_on` não é publicado. Religue pelo painel do DigitalOcean (página do Droplet, controle de
energia) ou pela API, com a action `power_on` e o token de escrita.

Droplet desligado continua sendo cobrado. Ao fim do capítulo, destrua os Droplets do laboratório
com o script de `setup/` do `09`; os valores estão na página de preços do DigitalOcean.

## Verificação

### Suíte de testes

```bash
uv run pytest
```

Os testes de escrita rodam offline, com um cliente falso no lugar do `pydo`:

- o esquema publica só os três nomes e recusa `db-producao` antes da função;
- `worker-01` sem a tag do laboratório é recusado sem disparar action;
- nome duplicado na tag é recusado sem disparar action;
- o shutdown dispara uma única action `shutdown` e o retorno declara o efeito;
- Droplet já desligado não dispara action;
- não há ferramenta de `power_off`, `reboot` nem de destruir no catálogo;
- as anotações de leitura e escrita aparecem no catálogo.

O teste que desliga um Droplet de verdade só roda com o token de escrita **e** com o nome do
Droplet de teste na linha de comando. Ter o token no `.env` não basta. Use um Droplet **ativo**
(`web-01` ou `worker-01`; o `batch-01` já fica desligado) e religue-o depois:

```bash
DROPLET_TESTE=worker-01 uv run pytest -k desliga_o_droplet_de_teste
```

### MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv run servidor-operacao
```

Veja o `enum` e as anotações de `desligar_droplet` na listagem de ferramentas.

## Pré-requisitos

- Python 3.12 e `uv`;
- chave da API da Anthropic;
- um token do DigitalOcean com `droplet:read` e outro com `droplet:read` e `droplet:update`;
- Droplets do laboratório criados pelo `setup/` do `09`;
- Node.js e `npx`, só para o Inspector;
- Claude Code, só para o segundo cliente.

## O que este exemplo não faz

- Não publica `power_off`, `power_on`, `reboot`, destruir nem ação genérica.
- Não implementa autorização por ação, aprovação humana, auditoria nem validação de conteúdo.
- Não filtra ferramentas no cliente: o agente recebe o catálogo inteiro.
- Não acompanha a action até o fim: declara o status no momento do disparo.
- Não sobe o server por HTTP, não adiciona autenticação, middleware, retry ou cache.

## Arquivos

```text
src/servidor.py          MCP server: leitura com escopo declarado e a escrita recortada
src/agente.py            cliente LangChain, igual ao do 14
dados/                   chamados, runbooks e histórico de mudanças fictícios
tests/test_servidor.py   recorte da escrita e efeito declarado, pelo cliente MCP em memória
.mcp.json                o mesmo server registrado para o Claude Code
.env.example             chave da API, modelo e os dois tokens do DigitalOcean
PLANO_TESTE.md           validação manual da demonstração
pyproject.toml           dependências e comandos `servidor-operacao` e `agente-operacao`
```
