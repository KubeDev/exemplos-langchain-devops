# Plano de teste · inventário de Droplets

Roteiro manual para validar o exemplo antes da gravação. Rode tudo de dentro de
`09-inventario-droplets`.

## 1. Instalação e estrutura

- [ ] `uv sync --locked` conclui sem alterar `uv.lock`.
- [ ] `uv run python -c "import src.inspecionar"` conclui (o `src.app` exige as chaves no `.env`).
- [ ] Os comandos instalados se chamam `inventario-droplets` e `inspecionar`.
- [ ] `.env`, `.venv` e caches estão ignorados (`git status` não os lista).

## 2. Preparação da conta DigitalOcean

O exemplo só lê. Criar e apagar Droplets é preparação, feita pelos scripts de `setup/` com o
`pydo` e um token separado.

- [ ] `DIGITALOCEAN_TOKEN` no `.env`: token com escopo customizado, só `droplet:read`.
- [ ] `DIGITALOCEAN_TOKEN_SETUP` no `.env`: token com `droplet:create`, `droplet:read`,
      `droplet:update`, `droplet:delete`, `tag:create` e `tag:read`.
- [ ] O script cria o laboratório da tabela e termina listando região, id, status, nome,
      memória e tags:

| Droplet | Região | Memória | Estado |
|---|---|---|---|
| `web-01` | `nyc1` | 2 GB | `active` |
| `worker-01` | `nyc1` | 1 GB | `active` |
| `batch-01` | `sfo3` | 1 GB | `off` |

- [ ] `batch-01` termina `off` (o log mostra o `shutdown`, ou o `power_off` se o shutdown não
      concluir).
- [ ] Rodar de novo não recria: cada nome aparece como "Já existe, não recriado", e um estado
      fora da tabela é corrigido com aviso.

```bash
uv run setup/criar_droplets.py
```

- [ ] No painel, os três Droplets aparecem com Monitoring ativo.
- [ ] Se a API recusar o tamanho ou a imagem, confira os slugs disponíveis na região e ajuste
      `IMAGEM` ou o tamanho e a região em `DROPLETS` no script.

## 3. O que o modelo recebe

- [ ] `uv run inspecionar` mostra as duas formas, e `uv run inspecionar N` mostra uma só.
- [ ] Forma 1: o bloco `Args:` aparece dentro de `description`; os quatro argumentos aparecem
      só com tipo no `input_schema`, sem `description`, `pattern`, `enum` nem `minimum`.
- [ ] Forma 2: `description` só com a frase da ferramenta; cada argumento com `description`;
      `regiao` com `pattern` `^[a-z]{3}[0-9]$`, `status` com `enum` dos quatro status e as
      memórias com `minimum` 512.
- [ ] Na forma 2, nada no `input_schema` menciona a regra mínima ≤ máxima.

## 4. O agente

- [ ] `.env` com `ANTHROPIC_API_KEY` válida.
- [ ] Com o import padrão (`docstring`), a pergunta da demo:

```bash
uv run inventario-droplets "Quais Droplets ativos têm pelo menos 2 GB de memória?"
```

- [ ] O log mostra `status='active'` e `memoria_minima_mb=2048`, e, do laboratório, a resposta traz só `web-01` (outros Droplets da conta podem aparecer).
- [ ] Com perguntas que usem um filtro por vez, o laboratório cobre estes critérios (cada um
      deixa ao menos um Droplet do laboratório de fora):

| Filtro | Devolve, do laboratório |
|---|---|
| `regiao='nyc1'` | `web-01` e `worker-01` |
| `status='active'` | `web-01` e `worker-01` |
| `status='off'` | `batch-01` |
| `memoria_minima_mb=2048` | `web-01` |
| `memoria_maxima_mb=1024` | `worker-01` e `batch-01` |
| "Quais Droplets ativos têm pelo menos 2 GB de memória?" | `web-01` |

- [ ] Cada Droplet da resposta vem com os campos do resumo (`nome`, `regiao`, `tamanho`,
      `memoria_mb`, `ip_publico` etc.), não o JSON inteiro da API.

- [ ] Troque o import em `src/app.py` por `modelo_pydantic` e rode as mesmas perguntas: mesmas respostas.
- [ ] Volte o import para `docstring` antes da gravação.

## 5. Fronteiras

- [ ] Não há validação explícita, `try/except` de `ValidationError` nem script de valor inválido.
- [ ] Não há `bind_tools`, loop sobre `tool_calls` nem `ToolMessage`.
- [ ] Não há testes nem cliente simulado.
- [ ] A ferramenta devolve o resumo por Droplet, sem paginação.
- [ ] Nenhum recurso da conta é alterado pelo exemplo; o token do exemplo não tem escrita.

## 6. Depois da gravação

- [ ] Apagar os Droplets de teste, em todas as regiões (só os que têm a tag `inventario-droplets`):

```bash
uv run setup/destruir_droplets.py
```
