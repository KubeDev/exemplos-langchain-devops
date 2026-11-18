# 24 · Skills carregadas sob demanda

Um agente analisa um projeto escolhido numa interface web entre as pastas de `workspace/`:
`catalogo-api/` (uma API Node) e `pedidos-worker/` (um worker Node), os dois com Dockerfile e
manifestos do Kubernetes. Para revisar pelo padrão do time, ele usa **skills**: a de Docker e a
de Kubernetes, cada uma num `SKILL.md` em `workspace/skills/`, no formato
[Agent Skills](https://agentskills.io/).

O agente é um `create_agent` com dois middlewares prontos do pacote `deepagents`:

- **`FilesystemMiddleware`** dá ao agente `ls`, `read_file`, `write_file` e `edit_file` sobre a
  pasta `workspace/`. O `FilesystemBackend` com `virtual_mode=True` prende o acesso a ela: o
  agente vê `/catalogo-api`, `/pedidos-worker` e `/skills`, e nada fora disso (nem o `.env`).
- **`SkillsMiddleware`** lê o frontmatter de cada `SKILL.md` e põe no system prompt só o `name`, a
  `description` e o caminho de cada skill. O conteúdo da skill entra quando o modelo decide ler o
  `SKILL.md` com `read_file`.

O system prompt escrito no código não cita nenhuma skill.

| Arquivo | Papel |
|---|---|
| `src/agente.py` | backend, os dois middlewares e `criar_agente(projeto)`, que põe a pasta escolhida no system prompt |
| `src/web.py` | interface web: seleção do projeto, passo a passo ao vivo (chamadas, skill carregada, retorno das ferramentas) e o tamanho da thread a cada turno |
| `workspace/skills/` | as skills de Docker (com `referencia.md`) e de Kubernetes |
| `workspace/catalogo-api/`, `workspace/pedidos-worker/` | os projetos revisados, com os problemas de propósito |

## Executar

```bash
cp .env.example .env   # preencha ANTHROPIC_API_KEY
uv sync --locked
uv run streamlit run src/web.py
```

Escolha o projeto na barra lateral e pergunte. Enquanto o agente trabalha, cada passo aparece na
tela; ao terminar, o passo a passo fica recolhido acima da resposta:

```text
📘 skill carregada: docker
[model] chama read_file({'file_path': '/skills/docker/SKILL.md', 'limit': 1000})
[model] chama ls({'path': '/catalogo-api'})
[read_file]
---
name: docker
...
[thread] mensagens: 13 · skills no histórico: ['docker']
```

A barra lateral marca as skills que já estão no histórico da thread. Trocar de projeto começa uma
conversa nova.

Perguntas para comparar:

- `O que esse projeto faz?` lê arquivos do projeto e nenhum `SKILL.md`.
- `Analisa o Dockerfile` lê só a skill de Docker.
- Na mesma thread, `E os manifests do Kubernetes?` lê a de Kubernetes. As duas ficam no histórico.
- `Cria o .dockerignore` lê a referência da skill e escreve o arquivo.
- Troque para `pedidos-worker` e peça `Analisa o Dockerfile`: a mesma skill, outros problemas.
  Projeto novo é só uma pasta nova em `workspace/`.

As perguntas de correção alteram o projeto escolhido. Para voltar ao cenário inicial:
`git checkout -- workspace && git clean -fd workspace`.

## O que o exemplo mostra

- **Especializar não exige outro agente.** O mesmo agente ganha a especialidade quando precisa
  e continua falando com o usuário.
- **A `description` é o roteador.** É o que o modelo vê de cada skill antes de decidir ler.
- **Progressive disclosure em três níveis.** `name` e `description` sempre no contexto; o
  `SKILL.md` só quando a pergunta pede; a `referencia.md` só quando a skill manda.
- **Skill nova é pasta nova.** Nenhuma linha de código muda para acrescentar uma skill.
- **A skill cobra.** Chamadas a mais para ler, e o conteúdo fica na thread: não existe
  descarregar.
