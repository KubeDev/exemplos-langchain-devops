# 17 · Agente de onboarding com RAG

Quem chega no time precisa achar o procedimento certo do projeto certo sem procurar à mão. Este exemplo
liga uma base de documentação ao agente e mostra as duas formas de fazer isso:

- **busca fixa (2-Step RAG)**: a aplicação busca sempre, antes do modelo, e entrega os trechos junto com a pergunta;
- **busca como ferramenta (Agentic RAG)**: o agente decide se busca e monta o filtro de metadado (`projeto`, `tipo`)
  a partir da conversa. Quando a pergunta não diz o projeto e a resposta depende dele, ele pergunta.

A recuperação combina **filtro por metadados com busca por similaridade**: o metadado restringe os candidatos, a
similaridade ordena dentro deles. Quando é o modelo que monta o filtro, o nome do padrão é *self-querying*.

O código está separado pelo papel de cada parte, para o aluno ver onde termina uma e começa a outra:

| Arquivo | Papel |
|---|---|
| `ingestao.py` | **ingestão**: o documento vira chunks com metadado, que viram embeddings no pgvector |
| `agente.py` | **consumo**: o agente usa o índice, com a busca fixa ou com a busca como ferramenta |
| `web.py` | **interface**: as páginas de ingestão e de chat, as rotas, os formulários e as sessões |

As duas páginas ficam na mesma aplicação web, com um menu para alternar entre elas. Num sistema real, ingestão e
chat seriam aplicações separadas; aqui ficam juntas para facilitar a demonstração. Cada sessão do chat é uma thread no
checkpointer do PostgreSQL.

A base em `dados/` é a documentação fictícia de dois projetos reais da KubeDev, descritos no estado atual dos
repositórios: [kube-news](https://github.com/KubeDev/kube-news) (commit `aab9356`) e
[encontros-tech](https://github.com/KubeDev/encontros-tech) (commit `0f5bbad`). São 18 documentos: guia, referência,
runbooks e post-mortems de cada projeto, mais um documento de entrada. Os dados de produção dos post-mortems são
simulados.

## Preparação

Use Python 3.12, `uv`, Docker, o [Ollama](https://ollama.com) e uma chave da API da Anthropic. Nesta pasta:

```bash
cp .env.example .env            # preencha ANTHROPIC_API_KEY
uv sync --locked
docker compose up -d --wait     # PostgreSQL com pgvector em 127.0.0.1:55437 e pgweb em http://localhost:58437
ollama pull qwen3-embedding:0.6b
```

Suba a aplicação web:

```bash
uv run web                      # http://127.0.0.1:8002
```

Na página **Ingestão**, envie todos os arquivos de `dados/` (as duas subpastas e o `projetos-do-time.md`).

## Configuração

| Variável | O que muda |
|---|---|
| `MODO_BUSCA` | `fixa` (2-Step) ou `ferramenta` (Agentic) |
| `K` | quantos trechos cada busca devolve |
| `MODELO` | o modelo da Anthropic que responde |
| `COLECAO` | a coleção do pgvector |

O `.env` é lido na subida: reinicie a aplicação depois de mudar. Para um teste rápido sem editar o arquivo, a variável
do ambiente vale mais que a do `.env`: `MODO_BUSCA=fixa uv run web`.

## Percurso da aula

1. **Ingestão.** Envie a base e veja a tabela com projeto, tipo e chunks de cada documento. Reenvie um arquivo: ele
   aparece como `atualizado`, com os chunks antigos trocados pelos novos. No pgweb
   (<http://localhost:58437>), a aba *Query* mostra os metadados que o filtro da busca usa:
   ```sql
   SELECT cmetadata->>'source' AS origem, cmetadata->>'projeto' AS projeto,
          cmetadata->>'tipo' AS tipo, cmetadata->>'secao' AS secao
   FROM langchain_pg_embedding ORDER BY projeto, origem;
   ```
   As tabelas `checkpoint*` ao lado são as sessões do chat.
2. **Busca fixa.** Com `MODO_BUSCA=fixa`, pergunte `A aplicação não conecta no banco. O que eu faço?`. A busca não
   tem filtro, porque ninguém escolhe o projeto antes dela. Veja no terminal de onde vieram os trechos e abra
   "Trechos gravados nesta mensagem": eles ficam na thread.
3. **Busca como ferramenta.** Com `MODO_BUSCA=ferramenta`, faça a mesma pergunta numa sessão nova. O agente pergunta
   o projeto. Responda `kube-news` e veja a chamada `buscar_documentos(..., projeto='kube-news')` na página e o filtro
   no terminal. Pergunte `Isso já aconteceu antes?`: a resposta vem dos post-mortems, sem perguntar o projeto de novo.
4. **Sessões.** Crie uma sessão nova: o agente não sabe mais o projeto. Carregue a sessão anterior pela lista.
   Reinicie a aplicação: as sessões continuam.
5. **Quantidade de trechos.** Repita uma pergunta com `K=1` e com `K=12` e compare a resposta e os caracteres
   recuperados no terminal.

A resposta do modelo varia. O que a aula mostra é o que muda na estrutura: quem decide buscar, qual filtro foi
aplicado, quais fontes vieram e o que ficou gravado na sessão.

## Onde está cada coisa

- `src/agente_onboarding/agente.py`: **o consumo pelo agente**. O retriever, a busca fixa, a ferramenta de busca com
  filtro e os prompts;
- `src/agente_onboarding/ingestao.py`: **a ingestão**. O frontmatter, a divisão em chunks e a gravação no pgvector;
- `src/agente_onboarding/web.py`: **a interface**. As duas páginas, as sessões e a leitura do histórico no
  checkpointer; `templates/` e `static/` são o HTML e o CSS;
- `dados/`: a base de documentos;
- `compose.yaml`: PostgreSQL com pgvector, usado pelo índice e pelo checkpointer, e pgweb para consultar o banco.
