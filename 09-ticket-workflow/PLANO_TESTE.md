# Plano de teste manual

Roteiro para validar o exemplo do zero. São ~5 minutos e ~US$ 0,08 em chamadas de API.

Marque cada `[ ]` conforme executa. Onde um critério pode falhar, o item **Se falhar** logo
abaixo diz o que investigar.

> Latência e texto dos relatórios variam — o modelo não é determinístico. O que **não** pode
> variar é a categoria de cada cenário e a quantidade de tickets gerados.

---

## Parte 0 · Preparação

- [ ] **0.1** — `uv --version` responde (se não: https://docs.astral.sh/uv/)
- [ ] **0.2** — `uv sync` conclui sem erro
- [ ] **0.3** — `cp .env.example .env` e preencher `ANTHROPIC_API_KEY`
- [ ] **0.4** — Limpar execuções anteriores: `rm -f tickets/*/*.md`
- [ ] **0.5** — Subir o servidor: `uv run uvicorn src.main:app --reload`
- [ ] **0.6** — Em outro terminal: `curl -s localhost:8000/saude` → `{"status":"ok"}`

> **Deixe o terminal do servidor visível.** O corpo da resposta HTTP é só o resumo; a
> validação de verdade é o log.

---

## Parte 1 · Cenário 1 — rota de infra

Dispare o cenário **1** do `cenarios.http`, ou:

```bash
curl -X POST localhost:8000/webhook/alerta \
  -H 'Content-Type: application/json' -d @exemplos/alerta_infra.json
```

- [ ] **1.1** — Bloco `TRIAGEM` mostra `modelo: claude-haiku-4-5`
- [ ] **1.2** — Aparece um `raciocinio` de uma frase **antes** da categoria
- [ ] **1.3** — `categoria: infra`
- [ ] **1.4** — Roda **apenas** `ANALISTA INFRA`, com `modelo: claude-sonnet-5`
- [ ] **1.5** — `ls tickets/infra/` → 1 arquivo · `ls tickets/desenvolvimento/` → vazio

> **Se falhar 1.2** (não aparece raciocínio): o `SYSTEM_TRIAGEM` em `prompts.py` foi alterado. As duas
> linhas — frase, depois palavra — são o que faz a triagem acertar os casos difíceis; sem
> elas o modelo responde no reflexo. Veja "Três coisas que a validação ensinou" no README.

---

## Parte 2 · Cenário 2 — a outra rota

```bash
curl -X POST localhost:8000/webhook/alerta \
  -H 'Content-Type: application/json' -d @exemplos/alerta_dev.json
```

- [ ] **2.1** — `categoria: desenvolvimento`
- [ ] **2.2** — Roda apenas `ANALISTA DEV`
- [ ] **2.3** — 1 novo arquivo em `tickets/desenvolvimento/`, nada novo em `infra/`

**O ponto do cenário:** as chains são exatamente as mesmas do cenário 1. Mudou o dado, mudou
a categoria, e o `if` levou a outro lugar.

---

## Parte 3 · Cenário 3 — os dois especialistas *(o mais importante)*

```bash
curl -X POST localhost:8000/webhook/alerta \
  -H 'Content-Type: application/json' -d @exemplos/alerta_ambiguo.json
```

- [ ] **3.1** — `categoria: ambos`
- [ ] **3.2** — O `raciocinio` menciona os **dois** domínios
- [ ] **3.3** — Rodam `ANALISTA INFRA` **e** `ANALISTA DEV`
- [ ] **3.4** — `relatorios: 2` no bloco de gravação
- [ ] **3.5** — **2 arquivos**, um em cada pasta
- [ ] **3.6** — Tempo total ~30s — os dois analistas rodam em sequência, não em paralelo

**O teste que mais importa** — abra os dois `.md` recém-criados:

- [ ] **3.7** — As **seções são diferentes**: o de infra tem `## Recurso afetado` e
      `## Time destino`; o de dev tem `## Mudanca suspeita` e `## Code owner`
- [ ] **3.8** — Os **Passos de investigação** propõem ações diferentes (ex.: infra questiona
      o critério do rightsizing; dev vai para heap dump e refatorar a exportação)

> **Se falhar 3.1** (não deu `ambos`): não mexa no classificador antes de checar o payload.
> `exemplos/alerta_ambiguo.json` foi calibrado para ter evidência concreta nos **dois**
> domínios — o `LimitRange` reduzido de 1Gi para 512Mi (infra) e o `ExportService` carregando
> 41 mil registros em memória (dev). Se um dos lados foi removido ou enfraquecido, o alerta
> deixou de ser ambíguo e a triagem está certa em escolher um lado.
>
> **Se falhar 3.7-3.8** (relatórios parecidos): é bug, mesmo que os dois estejam corretos —
> a lição depende da divergência. Os dois analistas recebem **exatamente o mesmo texto**; o
> que os diferencia são os system prompts em `prompts.py`, incluindo a lista de seções que
> cada um deve produzir. Se essas listas ficaram parecidas, os relatórios ficam também.

---

## Parte 4 · Cenário 4 — sem evidência nenhuma

```bash
curl -X POST localhost:8000/webhook/alerta \
  -H 'Content-Type: application/json' -d @exemplos/alerta_vago.json
```

- [ ] **4.1** — `categoria: ambos`, mas por motivo **oposto** ao do cenário 3: lá havia
      evidência dos dois lados, aqui não há evidência de lado nenhum
- [ ] **4.2** — 2 arquivos gerados

**Anti-alucinação** — abra os dois `.md`:

- [ ] **4.3** — A seção `## Evidencia` diz
      *"Nenhuma evidencia direta no alerta — a causa provavel acima e hipotese"*
- [ ] **4.4** — A seção `## Causa provavel` está formulada como hipótese, não como fato

> **Se falhar 4.3** (o modelo inventou log): a instrução anti-alucinação nos system prompts
> de `prompts.py` foi enfraquecida. É o critério mais importante desta parte — um ticket com
> causa raiz inventada custa a hora mais cara da empresa.

---

## Parte 5 · Verificação final

- [ ] **5.1** — 4 chamadas geraram **6 tickets** (1 + 1 + 2 + 2)
- [ ] **5.2** — Nenhuma linha de log contém a chave de API
- [ ] **5.3** — Parar o servidor (`Ctrl+C`)
- [ ] **5.4** — Se a chave era temporária: `rm .env` e confirmar com `grep -ri "sk-ant" .`

### Teste opcional — robustez da triagem

A triagem devolve texto livre, então vale confirmar que ela generaliza em vez de ter
decorado os quatro payloads:

```bash
curl -X POST localhost:8000/webhook/alerta \
  -H 'Content-Type: application/json' \
  -d '{"titulo":"Latencia p99 acima de 4s no catalogo","servico":"catalogo-api",
       "severidade":"high",
       "logs":["HikariPool-1 - Connection is not available, request timed out after 30000ms",
               "postgres: duration: 3812ms statement: SELECT * FROM produtos WHERE categoria_id = $1",
               "config: pool de conexoes reduzido de 50 para 20 na semana passada"]}'
```

- [ ] **5.5** — Deve dar `ambos`: há mudança de plataforma (pool reduzido) **e** de código
      (consulta sem índice). Este payload não aparece em lugar nenhum dos prompts.

---

## Tabela de referência

Da validação em 20/07/2026 — compare categoria e contagem de tickets; tempo varia:

| # | Cenário | Categoria | Tickets | Tempo |
|---|---|---|---|---|
| 1 | infra | `infra` | 1 | 15,4s |
| 2 | dev | `desenvolvimento` | 1 | 17,5s |
| 3 | ambíguo | `ambos` | 2 | 32,1s |
| 4 | vago | `ambos` | 2 | 19,9s |

---

## Problemas conhecidos

| Sintoma | Causa | Solução |
|---|---|---|
| `400 · temperature is deprecated for this model` | Sampling params removidos em Sonnet 5 / Opus 4.7+ | Não passar `temperature` ao criar o modelo |
| `401 · authentication_error` | `ANTHROPIC_API_KEY` inválida | Conferir a chave no `.env` (lido por `load_dotenv()` em `main.py`) |
| `TypeError: Could not resolve authentication method` | Chave **vazia**: os modelos são criados no import de `chains.py`, então o `load_dotenv()` do `main.py` precisa vir **antes** desse import | Conferir se o `.env` existe e se o `load_dotenv()` está acima dos `from src....` |
| Criou/editou o `.env` e nada mudou | `--reload` observa só arquivos `.py` | Reiniciar o servidor |
| Cenário 3 dá `infra` ou `desenvolvimento` | Triagem sem espaço para raciocinar, ou payload desequilibrado | Ver "Se falhar 3.1" acima |
| Log sem o bloco `enviado aos prompts:` | `LOG_VERBOSE=0` | Definir `LOG_VERBOSE=1` no `.env` |
| Alterou o código e nada mudou | Servidor sem `--reload` | `uv run uvicorn src.main:app --reload` |
