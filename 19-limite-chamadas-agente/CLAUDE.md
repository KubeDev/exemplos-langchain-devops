# Contexto deste exemplo

Leia o `README.md` e o `CLAUDE.md` da raiz do repositório antes de alterar o projeto.

Exemplo `19` da série, primeiro do capítulo de Middleware e Guardrails. A lição é: **limite de
chamadas de modelo e de ferramenta como teto do laço sem progresso**, com os padrões
diferentes de cada um (o de modelo encerra a execução; o de ferramenta bloqueia a chamada e
deixa o modelo seguir).

- **Dois arquivos autocontidos, quase iguais de propósito.** `limite_modelo.py` e
  `limite_ferramenta.py` duplicam a ferramenta, o prompt e o `mostrar()`; só o middleware
  muda. A turma compara os dois lado a lado. Não extraia código comum.
- **A ferramenta é simulada e devolve sempre `provisioning`.** É o que garante o laço. Não a
  troque por API real nem por MCP.
- **Um middleware por arquivo, com os valores da demo.** Variações (`exit_behavior`, rodar sem
  middleware) são trocadas na tela pelo instrutor; não crie flag, `.env` nem modo para isso.
- **Sem `thread_limit` e sem checkpointer.** O escopo por conversa é explicado na
  documentação, não demonstrado.
- **Fora daqui:** `ToolErrorMiddleware` e `ToolRetryMiddleware` (próximo exemplo do capítulo),
  human-in-the-loop, PII e guardrail customizado.
- O log usa `agent.stream(..., stream_mode="updates")` para mostrar a etapa de cada mensagem,
  inclusive a do middleware. Ele é a interface da aula: não troque por `invoke`.
- **Provider:** chat Anthropic (`MODELO`, padrão `claude-haiku-5-5`). Sem `temperature`.
- Use `uv`.
