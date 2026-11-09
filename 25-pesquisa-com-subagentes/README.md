# 25 · Pesquisa com subagentes

Um **agente orquestrador** responde perguntas sobre os projetos do time sem pesquisar nada sozinho: ele delega a
dois **subagentes expostos como ferramentas**. Um pesquisa na internet; o outro consulta a documentação interna.

Cada subagente é um agente completo (modelo, instruções, ferramentas e formato de saída) embrulhado numa `@tool`.
O que atravessa a fronteira entre o orquestrador e o subagente é só o que o código passa:

- **na ida**, os argumentos da ferramenta. O subagente não vê a conversa, as ferramentas nem o estado do orquestrador;
- **na volta**, um retorno tipado, definido por um schema Pydantic no `response_format`. As páginas e os trechos que o
  subagente leu ficam do lado de lá.

Quando a pergunta precisa das duas fontes, o orquestrador chama os dois subagentes no mesmo turno, e eles rodam em
paralelo.

| Agente | Modelo | Alcança |
|---|---|---|
| orquestrador | `claude-sonnet-5-5` | só as duas ferramentas de subagente |
| `subagente_web` | `claude-haiku-5-5` | a busca na web (`TavilySearch`, a ferramenta pronta do `10`) |
| `subagente_docs` | `claude-haiku-5-5` | a busca na base interna (`buscar_documentos`, a ferramenta do `18`) |

A base em `dados/` é cópia fiel do [`18`](../18-agente-onboarding-tool): a documentação fictícia do
[kube-news](https://github.com/KubeDev/kube-news) e do [encontros-tech](https://github.com/KubeDev/encontros-tech).

## Preparação

Use Python 3.12, `uv`, Docker, o [Ollama](https://ollama.com), uma chave da API da Anthropic e uma do
[Tavily](https://app.tavily.com). Nesta pasta:

```bash
cp .env.example .env            # preencha ANTHROPIC_API_KEY e TAVILY_API_KEY
uv sync --locked
docker compose up -d --wait     # PostgreSQL com pgvector em 127.0.0.1:55439 e pgweb em http://localhost:58439
ollama pull qwen3-embedding:0.6b
uv run web                      # http://127.0.0.1:8004
```

Na página **Ingestão**, envie todos os arquivos de `dados/` (as duas subpastas e o `projetos-do-time.md`). O banco é
próprio deste exemplo, com portas diferentes das do `18`: os dois podem rodar ao mesmo tempo.

## A página

O chat tem duas colunas, uma de cada lado da fronteira:

- **Histórico do orquestrador**: o que ele viu. A conversa, as chamadas aos subagentes com os argumentos e o retorno
  tipado de cada um;
- **Bastidor dos subagentes**: o que ficou do outro lado. Por chamada, o que o subagente recebeu, as buscas que fez,
  quantos caracteres leu e quantos devolveu, e o horário de início e fim. A barra de cada chamada mostra a execução no
  tempo: barras sobrepostas são subagentes rodando juntos.

O bastidor fica em memória e não entra no estado do orquestrador. Reiniciar a aplicação apaga o bastidor; o histórico
continua no PostgreSQL.

## Percurso da aula

Numa sessão nova:

1. **Contrato de entrada.** Pergunte
   `Como a aplicação configura o SSL na conexão com o PostgreSQL e o que a documentação oficial do PostgreSQL recomenda?`.
   O orquestrador pergunta o projeto antes de delegar: o `subagente_docs` exige `projeto` no argumento e não tem como
   perguntar ao usuário.
2. **Dois subagentes no mesmo turno.** Responda `kube-news`. As duas chamadas saem juntas, as barras do bastidor se
   sobrepõem, e a resposta junta a configuração do kube-news com a recomendação da documentação oficial. Compare, no
   bastidor, os caracteres lidos com os devolvidos.

A resposta do modelo varia. Se a pergunta não nomear a tecnologia, a pesquisa na web depende do que a documentação
interna disser, e o orquestrador chama um subagente depois do outro: o paralelo depende de as sub-tarefas serem
independentes.

## Onde está cada coisa

- `src/pesquisa_com_subagentes/ferramenta_subagente_web.py`: **o subagente de web**. O schema, o agente de dentro e a
  ferramenta que o embrulha;
- `src/pesquisa_com_subagentes/ferramenta_subagente_docs.py`: **o subagente de documentos**, com a mesma forma, e a
  busca na base do `18`;
- `src/pesquisa_com_subagentes/agente_orquestrador.py`: **o orquestrador**. Importa só as duas ferramentas;
- `src/pesquisa_com_subagentes/bastidor.py`, `web.py`, `templates/` e `static/`: a interface e o registro do bastidor;
- `src/pesquisa_com_subagentes/ingestao.py`: a ingestão, cópia do `18`;
- `compose.yaml`: PostgreSQL com pgvector, usado pelo índice e pelo checkpointer do orquestrador, e pgweb.
