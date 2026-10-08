# 11 · Duas ferramentas, uma colisão

O exemplo coloca uma segunda ferramenta ao lado da `listar_droplets` do `09`. A nova,
`verificar_saude`, consulta a carga dos Droplets no DigitalOcean Monitoring. As duas leem a
mesma conta, recebem o mesmo argumento (`regiao`) e respondem sobre os mesmos Droplets. Quando as
descrições são parecidas, o modelo não tem como saber qual chamar.

O ponto da aula é este: **colisão é uma propriedade do conjunto de ferramentas, não de uma delas**.
A `listar_droplets` funcionava sozinha. Ela só fica ambígua quando entra a vizinha, e a correção
é uma descrição que diz quando usar, quando não usar e qual ferramenta usar no lugar.

## Status × saúde

| Ferramenta | API | Responde |
|---|---|---|
| `listar_droplets` | `droplets.list` (`GET /v2/droplets`) | **Status**: `active`, `off`… e o resumo do `09` (nome, região, tamanho, memória, IP, tags) |
| `verificar_saude` | `monitoring.get_droplet_load1_metrics` (`GET /v2/monitoring/metrics/droplet/load_1`) | **Saúde**: load average de 1 minuto nos últimos 10 minutos, por Droplet |

`active` não quer dizer saudável. Um Droplet ligado com a CPU saturada aparece `active` no status
e com load alto no Monitoring. Em português, "situação" serve para as duas coisas, e é por isso que
"Qual a situação da web-01?" é a pergunta da demo.

A `verificar_saude` lista os Droplets como a `listar_droplets` (o mesmo `droplets.list`, filtrado
pela região) e busca a métrica de cada um pelo id. A resposta sai indexada pelo nome do Droplet, então cada ferramenta responde
sozinha a uma pergunta que cita a `web-01`.

Por que load average e não CPU: o endpoint de CPU devolve várias séries por modo (`idle`, `user`,
`system`…), que o modelo teria de combinar para chegar a uma porcentagem. O `load_1` é uma série só
por Droplet, legível na tela e no contexto do modelo.

## As duas versões do inventário

| Arquivo | Descrições |
|---|---|
| `src/ferramentas/ambiguas.py` | Parecidas: "Consulta os Droplets da conta DigitalOcean." × "Consulta a situação dos Droplets da conta DigitalOcean." |
| `src/ferramentas/contrastivas.py` | Cada uma diz quando usar, quando não usar e aponta a vizinha |

Os dois arquivos têm as mesmas ferramentas, com os mesmos nomes, argumento e corpo. **Só as
docstrings mudam.** Confira:

```bash
diff src/ferramentas/ambiguas.py src/ferramentas/contrastivas.py
```

E veja o que o modelo recebe de cada versão, sem chamar a DigitalOcean nem o modelo:

```bash
uv run inspecionar                # as duas versões
uv run inspecionar contrastivas   # só uma
```

A execução vive fora das declarações: `src/droplets.py` é o mesmo do `09` e `src/saude.py` tem a
consulta ao Monitoring. As ferramentas daqui recebem só `regiao`; os outros filtros do `09` ficam
em `None`, porque a lição é colisão, não esquema.

## O agente

`src/app.py` registra as duas ferramentas com `create_agent`. A versão do inventário é escolhida
por **uma linha de import**:

```python
from src.ferramentas.ambiguas import listar_droplets, verificar_saude
```

Cada ferramenta imprime o que o modelo pediu. Essa linha é o diagnóstico: a chamada pedida mostra
qual ferramenta o modelo escolheu e com qual argumento.

```text
Ferramenta: verificar_saude(regiao=None)
Ferramenta: listar_droplets(regiao=None, status=None, memoria_minima_mb=None, memoria_maxima_mb=None)
```

Rode a mesma pergunta algumas vezes com cada versão e compare as linhas `Ferramenta:`:

```bash
uv run inventario-droplets-colisao "Qual a situação da web-01?"
```

Com `ambiguas`, a escolha varia entre as execuções. Com `contrastivas`, fica estável.

Quando a pergunta pede as duas coisas ("a web-01 está ligada e com a carga normal?"), chamar as
duas ferramentas é o comportamento certo: isso é composição, não colisão.

## O token da DigitalOcean

O token do `09` tinha só `droplet:read`. A `verificar_saude` precisa ler métricas, então o token
deste exemplo ganha um escopo a mais: **`droplet:read` + `monitoring:read`**. Cada ferramenta nova
amplia o que o agente alcança na conta; o escopo cresce só no que a ferramenta precisa, e continua
só de leitura.

1. No painel da DigitalOcean, abra **API** e clique em **Generate New Token**.
2. Dê um nome e uma validade ao token.
3. Em escopos, escolha **Custom Scopes** e marque `droplet:read` e `monitoring:read`.
4. Copie o token na hora (ele não aparece de novo) e cole em `DIGITALOCEAN_TOKEN` no `.env`.

Se vazar, revogue no mesmo painel e gere outro.

## Preparação dos Droplets

Os scripts de `setup/` são os mesmos do `09` e servem aos dois exemplos. A tag `inventario-droplets`
é só a marca do cenário, usada pelo destruir; as ferramentas filtram por região. Eles usam o token `DIGITALOCEAN_TOKEN_SETUP` (`droplet:create`, `droplet:read`,
`droplet:update`, `droplet:delete`, `tag:create` e `tag:read`), que o agente nunca recebe.

```bash
uv run setup/criar_droplets.py     # nyc1: web-01 (2 GB) e worker-01 · sfo3: batch-01 (desligado)
uv run setup/destruir_droplets.py  # apaga só os Droplets com a tag inventario-droplets, em todas as regiões
```

Os Droplets são criados com `monitoring: true`, que instala o agente de Monitoring (`do-agent`).
Sem esse agente não há métrica para devolver. Depois de criados,
espere alguns minutos até as métricas aparecerem: a janela da `verificar_saude` é de 10 minutos.

Droplet desligado continua sendo cobrado: rode o destruir ao terminar. Os valores atuais estão na
página de preços da DigitalOcean.

## Como rodar

```bash
cp .env.example .env      # preencha ANTHROPIC_API_KEY e DIGITALOCEAN_TOKEN
uv sync

uv run inspecionar
uv run inventario-droplets-colisao "Qual a situação da web-01?"
```

## O que este exemplo não faz

- Não junta as duas ferramentas numa só nem adiciona parâmetro para escolher entre elas.
- Não conta acertos nem mede a escolha do modelo em lote: isso é avaliação, outra camada.
- Não abre o ciclo de tool calling com `bind_tools`: a chamada pedida aparece no log da ferramenta.
- Não trata erro nem diferencia retorno vazio de sucesso.
- Não recorta a resposta do Monitoring: a `verificar_saude` devolve a série completa por Droplet.
- Não testa as ferramentas sem a DigitalOcean.

## Arquivos

```text
src/app.py                        agente; o import escolhe a versão do inventário
src/inspecionar.py                o que o modelo recebe de cada versão
src/droplets.py                   a listagem de Droplets, idêntica à do 09
src/saude.py                      a carga de cada Droplet no Monitoring
src/ferramentas/ambiguas.py       as duas ferramentas com descrições parecidas
src/ferramentas/contrastivas.py   as mesmas, com descrições contrastivas
.env.example                      chave da API, modelo e tokens da DigitalOcean
PLANO_TESTE.md                    validação manual e critérios de aceite da demo
setup/criar_droplets.py           cria os Droplets de teste (o mesmo do 09)
setup/destruir_droplets.py        apaga os Droplets de teste (o mesmo do 09)
pyproject.toml                    dependências e comandos `inventario-droplets-colisao` e `inspecionar`
```
