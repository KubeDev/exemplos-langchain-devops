# 09 · A mesma ferramenta, duas declarações

O exemplo troca os runbooks e o cluster por uma conta DigitalOcean. A ferramenta
`listar_droplets` consulta os Droplets da conta, com filtros opcionais por região, status e
faixa de memória, e aparece **declarada de duas formas**. A execução é uma função só, em
`src/droplets.py`; as duas formas apenas a declaram e a chamam. Muda só o que o modelo recebe.

O ponto da aula é este: **o modelo não lê a sua função, lê o esquema gerado a partir dela**.
A forma de declarar decide onde as regras dos argumentos moram: em prosa ou no esquema.

## As duas formas

| # | Arquivo | Declaração | O que chega ao modelo |
|---|---|---|---|
| 1 | `src/ferramentas/docstring.py` | `@tool` com bloco `Args:` | Só os tipos; todas as regras viram prosa na descrição da ferramenta |
| 2 | `src/ferramentas/modelo_pydantic.py` | `args_schema` com o `BaseModel` `FiltroDroplets` | Cada campo com descrição e restrição: `pattern`, `enum`, `minimum` |

As regras são as mesmas nas duas:

| Argumento | Regra | Na forma 2 |
|---|---|---|
| `regiao` | slug minúsculo, como `nyc1` | `pattern` `^[a-z]{3}[0-9]$` |
| `status` | `new`, `active`, `off` ou `archive` | `enum` |
| `memoria_minima_mb` · `memoria_maxima_mb` | no mínimo 512 | `minimum` 512 |
| as duas memórias | mínima menor ou igual à máxima | `model_validator`, **fora do esquema** |

Na forma 1 as regras são texto que o modelo pode ou não seguir. Na forma 2 elas são parte do
esquema, com uma exceção: a regra entre campos (mínima ≤ máxima) é um `model_validator` e
**não aparece no JSON Schema** que o modelo recebe. Ela só é imposta quando o Pydantic valida
os argumentos, antes de a função rodar.

A API de listagem da DigitalOcean não filtra por esses campos, então `src/droplets.py` lista os
Droplets e filtra na aplicação. Argumento fora da regra não casa com nenhum Droplet: com
`regiao='NYC-1'` ou com mínima 2048 e máxima 1024, a forma 1 devolve `[]` sem erro, e a forma 2
nem chega a executar.

O retorno é um resumo por Droplet, não o JSON inteiro da API: `id`, `nome`, `status`, `regiao`,
`tamanho`, `vcpus`, `memoria_mb`, `disco_gb`, `ip_publico`, `tags` e `criado_em`.

## Inspecionando o que o modelo recebe

`src/inspecionar.py` converte cada forma no formato que o `ChatAnthropic` envia à API, com
`convert_to_anthropic_tool`, e imprime nome, descrição e `input_schema`:

```bash
uv run inspecionar        # as duas formas
uv run inspecionar 1      # só a forma 1
```

Nenhuma chamada à DigitalOcean ou ao modelo acontece aqui.

## O agente

`src/app.py` registra a ferramenta com `create_agent`. A forma usada é escolhida por **uma
linha de import**:

```python
from src.ferramentas.docstring import listar_droplets
```

Troque `docstring` por `modelo_pydantic` e rode de novo. A ferramenta imprime os argumentos que
recebeu:

```text
Ferramenta: listar_droplets(regiao='nyc1', status=None, memoria_minima_mb=None, memoria_maxima_mb=None)
```

## O token da DigitalOcean

O exemplo usa um **token de acesso pessoal com escopo customizado**, não um token de acesso
total. O escopo do token é o limite do que o agente consegue fazer na conta, então ele recebe
só o que a ferramenta precisa: ler Droplets.

1. No painel da DigitalOcean, abra **API** e clique em **Generate New Token**.
2. Dê um nome e uma validade ao token.
3. Em escopos, escolha **Custom Scopes** e marque só `droplet:read`.
4. Copie o token na hora (ele não aparece de novo) e cole em `DIGITALOCEAN_TOKEN` no `.env`.

O token fica fora do código, no `.env`, que está no `.gitignore`. Se vazar, revogue no mesmo
painel e gere outro.

## Preparação dos Droplets

Os scripts de `setup/` criam e apagam o cenário da aula com o `pydo`. Eles **escrevem** na
conta, por isso usam um segundo token, `DIGITALOCEAN_TOKEN_SETUP`, com mais escopo:
`droplet:create`, `droplet:read`, `droplet:update`, `droplet:delete`, `tag:create` e `tag:read`. O agente nunca
recebe esse token.

```bash
uv run setup/criar_droplets.py     # web-01 e worker-01 em nyc1, batch-01 em sfo3 (desligado)
uv run setup/destruir_droplets.py  # apaga, em todas as regiões, só os Droplets com a tag inventario-droplets
```

O laboratório é montado para que cada filtro tenha um Droplet que entra e um que fica de fora:

| Droplet | Região | Memória | Estado |
|---|---|---|---|
| `web-01` | `nyc1` | 2 GB | `active` |
| `worker-01` | `nyc1` | 1 GB | `active` |
| `batch-01` | `sfo3` | 1 GB | `off` |

Com ele, os filtros devolvem:

| Filtro | Devolve, do laboratório |
|---|---|
| `regiao='nyc1'` | `web-01` e `worker-01` |
| `status='active'` | `web-01` e `worker-01` |
| `status='off'` | `batch-01` |
| `memoria_minima_mb=2048` | `web-01` |
| `memoria_maxima_mb=1024` | `worker-01` e `batch-01` |
| "Quais Droplets ativos têm pelo menos 2 GB de memória?" | `web-01` |

Os três usam imagem Ubuntu, o agente de Monitoring ativo e uma tag com a função (`web`,
`worker`, `batch`). A tag `inventario-droplets` é só o recorte do laboratório para criar e
apagar; os filtros do agente são região, status e memória.

O criar não recria Droplet que já existe com o mesmo nome e a tag; se o estado não bate com a
tabela, ele liga (`power_on`) ou desliga e avisa. O `batch-01` é desligado com `shutdown`,
depois de ficar `active`; se o shutdown não concluir em cerca de 3 minutos, o script usa
`power_off`, aceitável num Droplet de laboratório recém-criado e sem carga. O destruir busca
pela tag, em todas as regiões.
Droplet desligado continua sendo cobrado: rode o destruir ao terminar. Os valores atuais estão
na página de preços da DigitalOcean.

## Como rodar

```bash
cp .env.example .env      # preencha ANTHROPIC_API_KEY e DIGITALOCEAN_TOKEN
uv sync

uv run inspecionar
uv run inventario-droplets "Quais Droplets ativos têm pelo menos 2 GB de memória?"
```

## O que este exemplo não faz

- Não valida argumentos na chamada nem mostra o que acontece com valor inválido.
- Não abre nem instrumenta manualmente o ciclo de tool calling.
- Não traz testes prontos: a pasta `tests/` é criada em aula por um agente de codificação, contra a
  conta real e sem cliente simulado.
- Não pagina a listagem: lê só a primeira página da API.
- Não ativa `strict` no provider.

## Arquivos

```text
src/app.py                          agente; o import escolhe a forma
src/inspecionar.py                  o que o modelo recebe de cada forma
src/droplets.py                     a consulta à DigitalOcean, comum às duas formas
src/ferramentas/docstring.py        forma 1
src/ferramentas/modelo_pydantic.py  forma 2
.env.example                        chave da API, modelo e tokens da DigitalOcean
setup/criar_droplets.py             cria os Droplets de teste
setup/destruir_droplets.py          apaga os Droplets de teste
pyproject.toml                      dependências e comandos `inventario-droplets` e `inspecionar`
```
