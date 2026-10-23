# 14 — Busca vetorial de documentos operacionais

Este exemplo indexa três runbooks em Markdown e três post-mortems em PDF no PostgreSQL com
pgvector. A indexação e a busca rodam em processos CLI distintos. A busca devolve o texto
recuperado, a origem e a distância de cosseno; nenhum resultado é enviado a um modelo de geração.
Os seis documentos são fictícios e não representam procedimentos de uma operação real.

## Preparação

Use Python 3.12, `uv`, Docker com Compose e uma chave da API da OpenAI. Nesta pasta:

```bash
cp .env.example .env
uv sync --locked
docker compose up -d --wait
```

Preencha `OPENAI_API_KEY` no `.env`. A porta local do banco é `55434`; o volume do Compose
preserva os dados depois que os processos Python terminam. A indexação chama a API de
embeddings da OpenAI e tem custo por tokens de entrada.

## Indexar

```bash
uv run indexar
```

O comando usa `carregar_markdown()` para ler cada runbook em UTF-8 e `carregar_pdf()`
para reunir o texto das três páginas de cada PDF com `pypdf`. Cada função devolve um
`Document` por arquivo. O fluxo comum gera embeddings com `text-embedding-3-small` em
1536 dimensões e os persiste. A primeira indexação produz **seis unidades recuperáveis**:
três Markdown e três PDFs inteiros. Cada execução substitui a coleção anterior.

## O que é um `Document` aqui

`Document` é o objeto de texto usado pelo LangChain na recuperação. Ele tem
`page_content` (texto), `metadata` (origem, formato e, no PDF, página) e um `id`
opcional. O nome `page_content` não exige que o texto seja uma página: na primeira versão,
cada runbook Markdown e cada PDF inteiro viram um `Document`. O PDF guarda a quantidade
de páginas em `metadata["pages"]`, mas não indica qual delas contém a resposta.
O embedding é calculado somente de `page_content`; o vetor é gravado ao lado do texto
e dos metadados no pgvector. A função de carregamento escolhe a unidade da busca.

## Buscar

Em outro processo, depois que `indexar` terminar:

```bash
uv run buscar "O consumidor da fila parou depois da troca da credencial. Como estabilizar?" --k 3
uv run buscar "O consumidor da fila parou depois da troca da credencial. Como estabilizar?" --k 6
```

`--k` limita a quantidade de resultados e vale 3 quando omitido. A CLI mostra a quantidade
de unidades e de caracteres recuperados antes do texto completo. Com `--k 6`, toda a base
volta à tela: é muito contexto para localizar uma ação específica. Cada resultado ainda
mostra origem e **distância de cosseno**: menor distância significa vetor mais próximo,
não uma porcentagem de relevância nem prova de que o texto responde à pergunta.

Na aula, a função `carregar_pdf()` é substituída pela versão do roteiro que cria um
`Document` por página. Depois de executar `uv run indexar` novamente, a mesma base passa
a ter **12 unidades**: três Markdown inteiros e nove páginas de PDF. Repita a busca com
`--k 3` e `--k 12`. A comparação mostra que o mesmo arquivo pode ocupar uma ou várias
posições no ranking, conforme a divisão feita antes do embedding. O PDF inteiro traz
texto demais; a página pode separar uma evidência da resolução do incidente. A Aula 07
mede divisões por conteúdo e tamanho para formar chunks recuperáveis.

O comando lê do banco o identificador e a dimensão do modelo usado na indexação. Se a
configuração de busca divergir, ele interrompe a consulta e orienta a reconstrução do
índice. O mesmo `text-embedding-3-small` converte os documentos e a pergunta.

## Arquivos

- `dados/`: três runbooks `.md` e três post-mortems `.pdf` fictícios;
- `src/busca_vetorial_pgvector/indexar.py`: extração, embedding LangChain e persistência;
- `src/busca_vetorial_pgvector/buscar.py`: compatibilidade, `k` e resultados;
- `compose.yaml`: PostgreSQL com pgvector e volume persistente.

O exemplo termina na recuperação. Estratégias de chunking, indexação incremental e uso
dos trechos pelo agente são assuntos das aulas seguintes.
