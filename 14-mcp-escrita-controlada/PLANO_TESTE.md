# Plano de teste — escrita controlada

## 1. Ambiente

- [ ] `uv sync` conclui sem alterar o lockfile.
- [ ] `.env` tem `ANTHROPIC_API_KEY`, `DIGITALOCEAN_TOKEN` e `DIGITALOCEAN_TOKEN_ESCRITA` sem aparecer no terminal.
- [ ] `DIGITALOCEAN_TOKEN` tem só `droplet:read`; `DIGITALOCEAN_TOKEN_ESCRITA` tem `droplet:read` e `droplet:update`, sem `droplet:delete`.
- [ ] Os Droplets do laboratório existem, com a tag `inventario-droplets` (`setup/criar_droplets.py` do `09`).
- [ ] `web-01` e `worker-01` em `nyc1`, ativos; `batch-01` em `sfo3`, desligado de propósito; um Droplet por nome na tag (a recusa por nome duplicado é proteção, coberta pelos testes offline).

## 2. Testes sem modelo

- [ ] `uv run pytest`: os testes offline passam; `test_listar_droplets_declara_pagina_e_total` (sem `DIGITALOCEAN_TOKEN`) e `test_desliga_o_droplet_de_teste` aparecem como `skipped`.
- [ ] Com o `.env` preenchido, `uv run pytest` continua **sem** desligar nada: o teste real segue `skipped` sem `DROPLET_TESTE`.
- [ ] `DROPLET_TESTE=worker-01 uv run pytest -k desliga_o_droplet_de_teste` passa e só o `worker-01` desliga (use um Droplet ativo).
- [ ] Religue o `worker-01` (painel do DigitalOcean ou API com o token de escrita, action `power_on`).

## 3. Ação permitida com efeito declarado

- [ ] `uv run agente-operacao` lista `desligar_droplet` entre as ferramentas.
- [ ] "Desligue o Droplet web-01 do laboratório.": o server registra `desligar_droplet(droplet='web-01')`.
- [ ] A resposta cita estado anterior, action `shutdown` disparada e a compensação com `power_on`.
- [ ] No painel, o `web-01` passa para `off`; nenhum outro Droplet muda.
- [ ] Repetir o pedido: o retorno diz que o Droplet já estava desligado e nenhuma action é disparada.

## 4. Valor fora do permitido

- [ ] "Desligue o Droplet db-producao.": o server recusa pela validação do esquema; nada é desligado.
- [ ] `listar_droplets(regiao='nyc1')` declara `filtro: regiao=nyc1` e `retornados: N de T` sobre o total da região.
- [ ] "Desligue o Droplet batch-01 do laboratório.": `batch-01` (em `sfo3`) é achado por nome e tag, sem região, e o retorno diz que já estava desligado, sem action.

## 5. Ação não publicada

- [ ] "Force o desligamento do web-01 com power_off.": não há ferramenta para isso; o agente diz que não pode.
- [ ] "Destrua o web-01.": idem.

## 6. Contrato e anotações

- [ ] Inspector mostra `operacao` versão `1.1.0`.
- [ ] `desligar_droplet` aparece com `enum` dos três nomes, `readOnlyHint: false` e `destructiveHint: true`.
- [ ] As ferramentas de leitura aparecem com `readOnlyHint: true`.

## 7. Encerramento

- [ ] Religue o `web-01` pelo painel ou pela API (action `power_on`).
- [ ] Ao fim do capítulo, destrua os Droplets do laboratório com `setup/destruir_droplets.py` do `09`.
- [ ] Nenhum segredo aparece em `.mcp.json`, código ou histórico do terminal.
