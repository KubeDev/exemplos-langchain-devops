# Contexto deste exemplo

Leia o `README.md` e o `CLAUDE.md` da raiz do repositório antes de alterar o projeto.

Exemplo `24` da série. A lição é: **usar skills num agente construído**. Dois middlewares prontos
do `deepagents` (`FilesystemMiddleware` e `SkillsMiddleware`) sobre um `create_agent`; as skills
são pastas com `SKILL.md`, lidas sob demanda.

- **O foco é usar a skill, não implementar o mecanismo.** Não escreva `load_skill`, loader de
  frontmatter nem middleware próprio de skill.
- **`create_agent`, não `create_deep_agent`.** Só as duas peças do `deepagents` que a aula usa; o
  harness inteiro é assunto do capítulo de Deep Agents.
- **O system prompt não cita skill.** A lista vem do `SkillsMiddleware`.
- **A raiz do backend é `workspace/`, com `virtual_mode=True`.** Nunca aponte o backend para a pasta
  do exemplo: o agente leria o `.env`.
- **Skills sem script.** São de análise e escrita de arquivo; não adicione `execute`, sandbox,
  `hadolint` ou `kubectl`.
- **`workspace/projeto-analisado/` tem os problemas de propósito** (`latest`, root, sem multi-stage,
  sem `.dockerignore`, sem probes e sem resources). Não corrija no repositório.
- **Fora daqui:** `metadata.include_tools` (ferramentas liberadas pela skill), subagente, handoff,
  roteador, memória de longo prazo e o restante do harness do Deep Agents.
- **Provider:** chat Anthropic (`MODELO`, padrão `claude-haiku-5-5`). Sem `temperature`.
- Use `uv`.
