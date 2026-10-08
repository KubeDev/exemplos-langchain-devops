# Plano de teste — retorno com escopo declarado

## 1. Ambiente

- [ ] `uv sync` conclui sem alterar o lockfile.
- [ ] `.env` tem `ANTHROPIC_API_KEY` e `DIGITALOCEAN_TOKEN` sem aparecer no terminal.
- [ ] O token do DigitalOcean tem escopo customizado `droplet:read`.

## 2. Testes sem modelo

- [ ] `uv run pytest` sem `DIGITALOCEAN_TOKEN`: testes de dados locais passam e `test_listar_droplets_declara_pagina_e_total` aparece como `skipped`.
- [ ] `uv run pytest` com `DIGITALOCEAN_TOKEN`: todos os testes passam.

## 3. Falha silenciosa (`sem_escopo`)

- [ ] O import em `src/servidor.py` aponta para `src.retornos.sem_escopo`.
- [ ] `uv run agente-operacao` com a pergunta sugerida no README registra `consultar_historico_mudancas(servico='fila-pedidos', horas=None)`.
- [ ] O agente conclui que não houve mudança recente na `fila-pedidos`, sem citar período.

## 4. Escopo declarado (`com_escopo`)

- [ ] Troque o import para `src.retornos.com_escopo`.
- [ ] A mesma pergunta: a resposta cita as últimas 24 horas consultadas.
- [ ] O agente chama de novo com `horas` maior, ou aponta que a mudança pode estar fora do período.
- [ ] Quando amplia, a resposta cita a `MUD-305` (biblioteca do consumidor, 03/10).

## 5. Droplets

- [ ] O laboratório do `09` está na conta: `web-01` e `worker-01` em `nyc1`, `batch-01` em `sfo3`.
- [ ] Com `com_escopo`, "quais Droplets estão na região nyc1?" registra `listar_droplets(regiao='nyc1', ...)` e o retorno mostra `filtro: regiao=nyc1` e `retornados: N de T` com T igual aos Droplets de `nyc1` no painel (2 no laboratório).
- [ ] "Quais Droplets existem na conta?" registra `listar_droplets` sem região e o retorno mostra `filtro: todas as regiões`, com Droplets de mais de uma região.
- [ ] No detalhe `resumido` (padrão), os Droplets aparecem como `nome (id)`, com status e região.
- [ ] "Qual a memória e o IP público do web-01?" leva o agente a pedir `detalhe='completo'`, que traz os campos principais (`tamanho`, `vcpus`, `memoria_mb`, `disco_gb`, `ip_publico`, `tags`, `criado_em`).
- [ ] "Liste os Droplets da nyc1, um por página": com `limite=1`, o retorno mostra `retornados: 1 de 2` e `proxima_pagina: 2` no laboratório, e o agente pede a próxima página ou declara o corte na resposta.

## 6. Contrato

- [ ] Inspector ou cliente em memória mostra `operacao` versão `1.0.0` no `serverInfo`.
- [ ] Trocar `PERIODO_PADRAO_HORAS` de 24 para 1 não muda o `inputSchema` de `consultar_historico_mudancas`, e a pergunta do `CH-1042` deixa de achar a `MUD-311` (15h25) sem escopo declarado.
- [ ] Com o valor 1, `uv run pytest`: `test_periodo_padrao_fora_do_esquema` continua verde; falham só `test_periodo_padrao_alcanca_a_mudanca_da_tarde` e `test_com_escopo_o_vazio_declara_o_recorte`. Volte para 24.

## 7. Fronteiras

- [ ] Nenhuma ferramenta escreve ou altera recursos.
- [ ] O server não escreve no stdout; os logs `Ferramenta: ...` saem pelo stderr.
- [ ] `MCP_CONFIG` e `.mcp.json` têm a mesma entrada `operacao`.
- [ ] Nenhum segredo aparece em `.mcp.json`, código ou histórico do terminal.
- [ ] O estado commitado volta para `sem_escopo`.
