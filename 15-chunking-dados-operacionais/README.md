# 15 — Chunking de dados operacionais

Este exemplo divide a documentação e os logs de três serviços fictícios em chunks, escolhendo a
estratégia pela natureza de cada dado, gera os embeddings, grava no PostgreSQL com pgvector e
busca por similaridade. Os comandos `runbook` e `log` mostram os cortes no terminal sem chamar a API.
Nenhum resultado é enviado a um modelo de geração.

Todos os dados são fictícios e não representam uma operação real.

## Preparação

Use Python 3.12, `uv`, Docker com Compose e uma chave da API da OpenAI. Nesta pasta:

```bash
cp .env.example .env
uv sync --locked
docker compose up -d --wait
```

Preencha `OPENAI_API_KEY` no `.env`. A porta local do banco é `55435`. A indexação chama a API
de embeddings da OpenAI e tem custo por tokens de entrada; `runbook` e `log` não precisam de
chave nem de banco.

## A base

| Dado | Arquivos | Natureza |
|---|---|---|
| Runbook, arquitetura, referência | `dados/RB-*.md`, `dados/ARQ-*.md`, `dados/REF-*.md` | texto com títulos Markdown |
| Post-mortem | `dados/PM-*.pdf` | texto extraído de PDF, sem estrutura |
| Log de aplicação | `dados/logs/*.jsonl` | um evento JSON por linha |

## As estratégias

| Estratégia | Função | Onde corta | Sobreposição |
|---|---|---|---|
| Por tamanho | `dividir_por_tamanho()` | a cada `tamanho` caracteres, preferindo parágrafo, linha e palavra | caracteres repetidos do fim do chunk anterior |
| Por seção | `dividir_por_secao()` | nos títulos Markdown; título, serviço e tipo vão no texto do chunk | não usa |
| Janela de tempo | `janelas_de_log()` | intervalo do relógio, só WARN e ERROR | segundos repetidos do fim da janela anterior |

A divisão por tamanho é o que a documentação do LangChain chama de recursive character splitting.
Para cortar num caractere de separação específico, informe `separators`.

## Ver os chunks sem gerar embedding

```bash
uv run runbook
uv run log
```

`runbook` divide o RB-381 por tamanho e por seção e mostra o chunk do passo 7, o que pede
aprovação explícita. `log` divide o log do payments-worker em janelas e mostra as do início do
incidente. Os dois rodam sem chave e sem banco. Os parâmetros são constantes no topo de cada arquivo:
troque `SOBREPOSICAO` para 200 em `runbook.py`, ou para 5 em `log.py`, e rode de novo.

## Indexar e buscar

```bash
uv run indexar
uv run buscar "A fila de cobrança parou depois da rotação da credencial do broker. Como reiniciar os workers do payments-worker com segurança?" --k 3
```

`indexar` usa `dividir_base()`: seção nos documentos Markdown, por tamanho nos post-mortems em PDF
(1000 com sobreposição de 200, ponto de partida) e janela de 60 segundos com sobreposição de 20
nos logs (hipótese a testar). Mostra os chunks por tipo com o maior de cada um e os caracteres
enviados ao modelo de embedding, e reconstrói a coleção `chunks` a cada execução. O maior chunk é a
medição: a seção não tem limite de tamanho porque a maior delas fica muito abaixo do limite do
modelo. `buscar` imprime os `k` chunks mais próximos com origem e distância.

## Um arquivo, uma leitura

Cada comando é um arquivo que se lê sozinho, de cima a baixo, sem importar nada de outro arquivo
do projeto. Por isso as funções de divisão aparecem duas vezes: em `runbook.py` e `log.py`, para a
demo, e em `indexar.py`, para a base inteira. A repetição é de propósito. Ao mudar uma estratégia,
mude nos dois lugares.
