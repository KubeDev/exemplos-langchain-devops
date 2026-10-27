# Contexto deste exemplo

Leia o `README.md` e o `CLAUDE.md` da raiz do repositório antes de alterar o projeto.

Este é o exemplo da Aula 09 de Memória e RAG: o retriever ligado ao agente como ferramenta (Agentic RAG), numa base
de onboarding de dois projetos da KubeDev. Continua o `17`, que tem a mesma base com a busca fixa (2-Step).

- **O código preza o entendimento do aluno, e cada arquivo tem um papel só.**
  - `ingestao.py`: a ingestão, sem nada de web. `ler_frontmatter()`, `dividir()`, `documentos_no_indice()` e `gravar()`.
  - `agente.py`: o consumo pelo agente, lido de cima a baixo. O banco vetorial, `formatar()`,
    `mostrar_busca()`, a ferramenta `buscar_documentos` e `responder()`, que entrega só a pergunta ao agente.
  - `web.py`: toda a interface, fora do escopo da aula. Uma aplicação Flask com as duas páginas (`/` chat,
    `/ingestao`) e um menu entre elas, as rotas, os formulários, as sessões e o histórico.
  Não leve lógica de busca ou de ingestão para o `web.py`, nem rota ou formulário para os outros dois. Ingestão e chat
  na mesma aplicação é uma escolha didática; num sistema real seriam separados.
- **Só a busca como ferramenta.** Não traga a busca fixa de volta nem um `MODO_BUSCA`: a comparação é com o `17`, e
  o código dos dois fica parecido de propósito para a turma comparar os arquivos.
- **Sem middleware.** É conteúdo do Cap 05. Os trechos voltam como `ToolMessage` e ficam gravados na thread; a página
  mostra a chamada da ferramenta e os trechos devolvidos (`<details>`). No `17` eles ficam na mensagem do usuário.
- **Nome do padrão:** Agentic RAG com recuperação por filtro de metadados combinado com similaridade (self-querying).
  Não chame de "RAG híbrido" nem de "busca híbrida": na Aula 05, Hybrid RAG é a arquitetura com validação, e busca
  híbrida é lexical com vetorial.
- **Uma ferramenta com filtro, não uma ferramenta por fonte.** "Uma ferramenta por fonte" é só uma alternativa
  explicada em aula.
- `projeto` e `tipo` da ferramenta são `Literal`: o esquema impede o modelo de inventar valor.
- **Uma instância de `PGVector` por módulo (`agente.py` e `ingestao.py`), criada na importação.** O agente pode pedir
  duas buscas em paralelo, e criar dois `PGVector` ao mesmo tempo quebra a definição das tabelas no SQLAlchemy.
- **Ingestão sem mecanismo de aula anterior:** nada de hash nem de comparação novo/alterado/igual (Aula 08). Reenviar
  um arquivo apaga os chunks dele e grava os novos. Sem remoção pela tela. Metadado: `source`, `projeto`, `tipo` e
  `secao`. O ID do chunk é `<coleção>/<arquivo>#<n>`. `ingestao.py`, `dados/` e os templates são cópia
  do `17`: ao mudar um, avalie o outro.
- **Memória de curto prazo:** `PostgresSaver` no mesmo banco do pgvector. O `thread_id` é a data e hora de criação, e
  sem `user_id` e sem Store (lição do `13`).
- **Providers:** chat Anthropic (`MODELO`, padrão `claude-haiku-5-5`) e embeddings locais pelo Ollama
  (`qwen3-embedding:0.6b`, 1024 dimensões). Sem `temperature`.
- **A base `dados/` descreve o estado atual dos repositórios** kube-news (`aab9356`) e encontros-tech (`0f5bbad`). Porta,
  variável, rota e comportamento saem do código versionado. Nada de Docker, Kubernetes ou CI: a evolução desses projetos
  é feita em outras aulas. Os post-mortems simulam um servidor Linux de produção (aplicação rodando direto, PostgreSQL
  gerenciado, Prometheus) e usam o formato real de log de cada aplicação. Ao mudar um documento, confira o fato no
  código com `git show <commit>:<arquivo>`.
- **Portas próprias** para rodar ao lado do `17`: PostgreSQL `55438`, pgweb `58438`, web `8003`.
- Use `uv`.
