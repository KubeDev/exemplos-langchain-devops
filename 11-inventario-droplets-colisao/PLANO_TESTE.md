# Plano de teste · colisão entre ferramentas

Roteiro manual para validar o exemplo antes da gravação. Rode tudo de dentro de
`11-inventario-droplets-colisao`.

## 1. Instalação e estrutura

- [ ] `uv sync --locked` conclui sem alterar `uv.lock`.
- [ ] `uv run python -c "import src.inspecionar"` conclui (o `src.app` exige as chaves no `.env`).
- [ ] Os comandos instalados se chamam `inventario-droplets-colisao` e `inspecionar`.
- [ ] `.env`, `.venv` e caches estão ignorados (`git status` não os lista).
- [ ] `src/app.py` importa `ambiguas`.

## 2. Preparação da conta DigitalOcean

- [ ] `DIGITALOCEAN_TOKEN` no `.env`: escopo customizado com `droplet:read` e `monitoring:read`.
- [ ] `DIGITALOCEAN_TOKEN_SETUP` no `.env`: `droplet:create`, `droplet:read`, `droplet:update`,
      `droplet:delete`, `tag:create` e `tag:read`.
- [ ] Droplets de pé (`uv run setup/criar_droplets.py`, se faltarem; são os mesmos do `09`):
      `web-01` (`s-1vcpu-2gb-amd`) e `worker-01` em `nyc1`, ativos; `batch-01` em `sfo3`, desligado
      pelo script. O script pula o que já existe.
- [ ] No painel, `web-01` e `worker-01` aparecem com Monitoring ativo e já mostram gráficos.
- [ ] Os Droplets estão ligados há pelo menos 10 minutos: o agente de Monitoring precisa de alguns
      minutos para publicar as primeiras métricas, e a janela da `verificar_saude` é de 10 minutos.

### Fragilidades conhecidas do Monitoring

- **Sem agente, sem métrica.** Quando o `do-agent` não está instalado ou ainda não publicou nada,
  a série esperada é `result` vazio (confirmar na primeira execução com token). O setup cria os Droplets com
  `monitoring: true`; se usar Droplets criados de outra forma, instale o agente.
- **Droplet desligado não publica.** O `batch-01` fica `off`, então a `verificar_saude` mostra a
  série vazia (ou só pontos antigos) para ele. Isso não atrapalha a colisão: a pergunta da demo cita
  a `web-01`, que está ativa, e a escolha da ferramenta acontece antes do resultado.
- **Escopo.** Sem `monitoring:read`, a chamada de métricas falha com erro de autorização e a execução termina
  com o traceback (o exemplo não trata erro, de propósito).

## 3. Mesmo esquema, só a descrição muda

- [ ] `diff src/ferramentas/ambiguas.py src/ferramentas/contrastivas.py` mostra só linhas de
      docstring.
- [ ] `uv run inspecionar` mostra, nas duas versões, `name` e `input_schema` iguais e
      `description` diferente.

## 4. A ferramenta de saúde

Invocada direto, sem modelo:

```bash
uv run python -c "from dotenv import load_dotenv; load_dotenv(); \
from src.ferramentas.ambiguas import verificar_saude; print(verificar_saude.invoke({'regiao': 'nyc1'}))"
```

- [ ] O log mostra `Ferramenta: verificar_saude(regiao='nyc1')`.
- [ ] A resposta é um objeto com as chaves `web-01` e `worker-01` (os de `nyc1`) e, em cada uma, `status: success` e
      `data.result` com uma série de pares `[timestamp, valor]`.
- [ ] Com `{'regiao': 'sfo3'}`, só `batch-01`, com a série vazia (está `off`); sem região (`{}`),
      os três. A métrica é buscada
      pelo id do Droplet (`host_id`), sem região, então funciona igual nas duas regiões.
- [ ] Com uma região sem Droplets (`{'regiao': 'ams3'}`), a resposta é `{}`.

## 5. Perguntas-sonda

Leia a **primeira** linha `Ferramenta:` de cada execução como a escolha do modelo. Se uma pergunta
com uma ferramenta certa também chamar a outra, isso conta como colisão.

| # | Pergunta | Esperada |
|---|---|---|
| P1 | "Qual a situação da web-01?" | `listar_droplets` |
| P2 | "Quais Droplets estão desligados?" | `listar_droplets` |
| P3 | "Algum Droplet está com carga alta?" | `verificar_saude` |

```bash
uv run inventario-droplets-colisao "Qual a situação da web-01?"
```

- [ ] **Ambíguas, P1, 5 execuções:** a escolha varia; em pelo menos uma, o modelo chama
      `verificar_saude` (sozinha ou primeiro).
- [ ] **Contrastivas, P1 e P2, 10 execuções cada:** só `listar_droplets`.
- [ ] **P3, 5 execuções, nas duas versões:** só `verificar_saude`.
- [ ] **Composição, contrastivas:** "A web-01 está ligada e com a carga normal?" chama as duas.
      Isso é o comportamento certo, não colisão.
- [ ] Cada execução termina em até ~20 s.
- [ ] Volte o import para `ambiguas` antes da gravação.

Se as ambíguas não oscilarem em P1 (5/5 na mesma ferramenta), a colisão não está acontecendo com o
modelo atual. Calibre mexendo **só nas docstrings das ambíguas** e repita as 5 execuções.

### Resultado observado (07/10/2026, `claude-sonnet-5`, P1)

| Descrições ambíguas (`listar_droplets` × `verificar_saude`) | Chamadas em 5 execuções |
|---|---|
| "Consulta a situação dos Droplets…" × "Verifica a situação dos Droplets…" | 5/5 as duas, sempre `listar_droplets` primeiro |
| "Consulta a situação e o estado dos Droplets…" nas duas | 5/5 as duas, sempre `listar_droplets` primeiro |
| **"Consulta os Droplets…" × "Consulta a situação dos Droplets…" (versão atual)** | 3/5 as duas com `listar_droplets` primeiro · 2/5 só `verificar_saude` |
| Contrastivas | 5/5 só `listar_droplets` |

Depois da troca do argumento `tag` por `regiao` (mesmas docstrings, 07/10/2026):

| Versão | Chamadas em 5 execuções |
|---|---|
| Ambíguas | 2/5 só `verificar_saude` · 2/5 as duas com `verificar_saude` primeiro · 1/5 as duas com `listar_droplets` primeiro |
| Contrastivas | 5/5 só `listar_droplets(regiao=None)` |

Descrições idênticas não bastaram: o modelo cobriu a dúvida chamando as duas ferramentas. A escolha
só ficou instável quando a palavra da pergunta ("situação") ficou apenas na descrição da vizinha.
Em validação anterior, as contrastivas fizeram 10/10 só `listar_droplets`.

P2, P3 e composição: pendentes.

## 6. Fronteiras

- [ ] Não há fusão das ferramentas, parâmetro discriminante, `bind_tools` nem loop de repetição.
- [ ] Não há `try/except`, contrato de retorno, cliente simulado nem testes.
- [ ] `listar_droplets` devolve o resumo do `09`; `verificar_saude`, a resposta completa do Monitoring.
- [ ] `diff ../09-inventario-droplets/src/droplets.py src/droplets.py` não mostra diferença.
- [ ] Não há `temperature`.
- [ ] Nenhum recurso da conta é alterado pelo exemplo; o token do exemplo não tem escrita.

## 7. Depois da gravação

- [ ] Apagar os Droplets de teste (só os que têm a tag `inventario-droplets`):

```bash
uv run setup/destruir_droplets.py
```
