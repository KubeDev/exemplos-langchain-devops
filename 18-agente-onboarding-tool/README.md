# 18 · Agente de onboarding com a busca como ferramenta

No [`17`](../17-agente-onboarding), a aplicação busca sempre, antes do modelo, e sem filtro: ninguém escolhe o
projeto antes da busca, e os trechos podem vir de qualquer um. Este exemplo usa a mesma base e a mesma interface, mas
entrega a busca ao agente como **ferramenta (Agentic RAG)**: ele decide se busca e monta o filtro de metadado
(`projeto`, `tipo`) a partir da conversa. Quando a pergunta não diz o projeto e a resposta depende dele, ele pergunta.

A recuperação combina **filtro por metadados com busca por similaridade**: o metadado restringe os candidatos, a
similaridade ordena dentro deles. Quando é o modelo que monta o filtro, o nome do padrão é *self-querying*.

O código está separado pelo papel de cada parte, para o aluno ver onde termina uma e começa a outra:

| Arquivo | Papel |
|---|---|
| `ingestao.py` | **ingestão**: o documento vira chunks com metadado, que viram embeddings no pgvector |
| `agente.py` | **consumo**: o agente usa o índice pela ferramenta de busca com filtro |
| `web.py` | **interface**: as páginas de ingestão e de chat, as rotas, os formulários e as sessões |

As duas páginas ficam na mesma aplicação web, com um menu para alternar entre elas. Num sistema real, ingestão e
chat seriam aplicações separadas; aqui ficam juntas para facilitar a demonstração. Cada sessão do chat é uma thread no
checkpointer do PostgreSQL.

A base em `dados/` é a mesma do `17`: a documentação fictícia de dois projetos reais da KubeDev, descritos no estado
atual dos repositórios: [kube-news](https://github.com/KubeDev/kube-news) (commit `aab9356`) e
[encontros-tech](https://github.com/KubeDev/encontros-tech) (commit `0f5bbad`). São 18 documentos: guia, referência,
runbooks e post-mortems de cada projeto, mais um documento de entrada. Os dados de produção dos post-mortems são
simulados.

## Preparação

Use Python 3.12, `uv`, Docker, o [Ollama](https://ollama.com) e uma chave da API da Anthropic. Nesta pasta:

```bash
cp .env.example .env            # preencha ANTHROPIC_API_KEY
uv sync --locked
docker compose up -d --wait     # PostgreSQL com pgvector em 127.0.0.1:55438 e pgweb em http://localhost:58438
ollama pull qwen3-embedding:0.6b
```

O banco é próprio deste exemplo, com portas diferentes das do `17`: os dois podem rodar ao mesmo tempo.

Suba a aplicação web:

```bash
uv run web                      # http://127.0.0.1:8003
```

Na página **Ingestão**, envie todos os arquivos de `dados/` (as duas subpastas e o `projetos-do-time.md`).

## Configuração

| Variável | O que muda |
|---|---|
| `K` | quantos trechos cada busca devolve |
| `MODELO` | o modelo da Anthropic que responde |
| `COLECAO` | a coleção do pgvector |

O `.env` é lido na subida: reinicie a aplicação depois de mudar. Para um teste rápido sem editar o arquivo, a variável
do ambiente vale mais que a do `.env`: `K=1 uv run web`.

## Percurso da aula

1. **Ingestão.** Envie a base e veja a tabela com projeto, tipo e chunks de cada documento. No pgweb
   (<http://localhost:58438>), a aba *Query* mostra os metadados que o filtro da busca usa:
   ```sql
   SELECT cmetadata->>'source' AS origem, cmetadata->>'projeto' AS projeto,
          cmetadata->>'tipo' AS tipo, cmetadata->>'secao' AS secao
   FROM langchain_pg_embedding ORDER BY projeto, origem;
   ```
2. **Busca como ferramenta.** Pergunte `A aplicação não conecta no banco. O que eu faço?`, a mesma pergunta do `17`.
   O agente pergunta o projeto antes de buscar. Responda `kube-news` e veja a chamada
   `buscar_documentos(..., projeto='kube-news')` na página e o filtro no terminal. O agente pode pedir mais de uma
   busca no mesmo turno: muitas vezes ele já chama uma segunda com `tipo='post-mortem'` para ver se o problema
   aconteceu antes.
3. **Filtro por tipo.** Pergunte `Isso já aconteceu antes?`. O projeto não é perguntado de novo, porque já está na
   conversa. Se o agente ainda não consultou os post-mortems, ele busca agora com `tipo='post-mortem'`; se já
   consultou no passo anterior, responde com os trechos que estão na thread, sem buscar. As duas saídas mostram a
   mesma coisa: buscar é decisão do agente.
4. **Sessões.** Crie uma sessão nova: o agente não sabe mais o projeto. Carregue a sessão anterior pela lista.
   Reinicie a aplicação: as sessões continuam.
5. **Quantidade de trechos.** Repita uma pergunta com `K=1` e com `K=12` e compare a resposta e os caracteres
   recuperados no terminal.

A resposta do modelo varia. O que a aula mostra é o que muda na estrutura em relação ao `17`:

| | `17` · busca fixa | `18` · busca como ferramenta |
|---|---|---|
| Quem decide buscar | a aplicação, sempre | o agente |
| Filtro | nenhum | `projeto` e `tipo`, montados pelo agente |
| Onde os trechos ficam na thread | na mensagem do usuário | na resposta da ferramenta (`ToolMessage`) |

## Onde está cada coisa

- `src/agente_onboarding_tool/agente.py`: **o consumo pelo agente**. O retriever, a ferramenta de busca com filtro e o
  prompt;
- `src/agente_onboarding_tool/ingestao.py`: **a ingestão**. O frontmatter, a divisão em chunks e a gravação no pgvector;
- `src/agente_onboarding_tool/web.py`: **a interface**. As duas páginas, as sessões e a leitura do histórico no
  checkpointer; `templates/` e `static/` são o HTML e o CSS;
- `dados/`: a base de documentos;
- `compose.yaml`: PostgreSQL com pgvector, usado pelo índice e pelo checkpointer, e pgweb para consultar o banco.
