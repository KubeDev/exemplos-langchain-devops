# Contexto deste exemplo

Leia o `README.md` e o `CLAUDE.md` da raiz do repositório antes de alterar o projeto.

Este é o exemplo da Aula 09 de Memória e RAG: o retriever ligado ao agente como etapa fixa (2-Step RAG), numa
base de onboarding de dois projetos da KubeDev.

- **O código preza o entendimento do aluno, e cada arquivo tem um papel só.**
  - `ingestao.py`: a ingestão, sem nada de web. `ler_frontmatter()`, `dividir()`, `documentos_no_indice()` e `gravar()`.
  - `agente.py`: o consumo pelo agente, lido de cima a baixo. O banco vetorial, `formatar()`,
    `mostrar_busca()` e `responder()`, que busca sempre, sem filtro, e entrega os trechos ao agente.
  - `web.py`: toda a interface, fora do escopo da aula. Uma aplicação Flask com as duas páginas (`/` chat,
    `/ingestao`) e um menu entre elas, as rotas, os formulários, as sessões e o histórico.
  Não leve lógica de busca ou de ingestão para o `web.py`, nem rota ou formulário para os outros dois. Ingestão e chat
  na mesma aplicação é uma escolha didática; num sistema real seriam separados.
- **Só a busca fixa.** A busca como ferramenta, com filtro por metadados montado pelo agente, é o `18`. Não antecipe:
  nada de ferramenta, filtro ou `MODO_BUSCA` aqui. A busca sem filtro, misturando os projetos, é o gancho do `18`.
- **Sem middleware.** É conteúdo do Cap 05. Na busca fixa, os trechos entram na mensagem do usuário, e por isso ficam
  gravados na thread. Essa consequência é mostrada na página (`<details>`) e faz parte da comparação com o `18`.
- **Uma instância de `PGVector` por módulo (`agente.py` e `ingestao.py`), criada na importação.** Criar dois
  `PGVector` ao mesmo tempo quebra a definição das tabelas no SQLAlchemy.
- **Ingestão sem mecanismo de aula anterior:** nada de hash nem de comparação novo/alterado/igual (Aula 08). Reenviar
  um arquivo apaga os chunks dele e grava os novos. Sem remoção pela tela. Metadado: `source`, `projeto`, `tipo` e
  `secao`. O ID do chunk é `<coleção>/<arquivo>#<n>`.
- **Memória de curto prazo:** `PostgresSaver` no mesmo banco do pgvector. O `thread_id` é a data e hora de criação, e
  sem `user_id` e sem Store (lição do `13`).
- **Providers:** chat Anthropic (`MODELO`, padrão `claude-haiku-5-5`) e embeddings locais pelo Ollama
  (`qwen3-embedding:0.6b`, 1024 dimensões). Sem `temperature`.
- **A base `dados/` descreve o estado atual dos repositórios** kube-news (`aab9356`) e encontros-tech (`0f5bbad`). Porta,
  variável, rota e comportamento saem do código versionado. Nada de Docker, Kubernetes ou CI: a evolução desses projetos
  é feita em outras aulas. Os post-mortems simulam um servidor Linux de produção (aplicação rodando direto, PostgreSQL
  gerenciado, Prometheus) e usam o formato real de log de cada aplicação. Ao mudar um documento, confira o fato no
  código com `git show <commit>:<arquivo>`.
- Use `uv`.
