# Contexto deste exemplo

Leia o `README.md` e o `CLAUDE.md` da raiz do repositório antes de alterar o projeto.

Exemplo `20` da série, segundo do capítulo de Middleware e Guardrails. A lição é: **erro de
ferramenta tratado no agente**. A exceção vira mensagem que o modelo lê (`ToolErrorMiddleware`),
só o erro transitório ganha nova tentativa com recuo exponencial (`ToolRetryMiddleware`), e
repetir uma escrita só é seguro porque a ferramenta é idempotente.

- **Dois arquivos autocontidos, quase iguais de propósito.** `erro_ferramenta.py` e
  `retry_ferramenta.py` duplicam o prompt, o `tratar_erro` e o `mostrar()`. Não extraia código
  comum.
- **A ferramenta é simulada.** Em `erro_ferramenta.py` ela sempre recusa a credencial
  (`PermissionError`); em `retry_ferramenta.py` as primeiras `FALHAS_SIMULADAS` chamadas estouram
  o tempo (`TimeoutError`). É o que torna o erro reproduzível. Não a troque por API real nem por
  MCP.
- **A ferramenta é escrita e idempotente na docstring** ("se já estiver desligado, não faz
  nada"). É o argumento da aula para o retry ser seguro. Não troque por leitura.
- **O `print` com horário dentro da ferramenta é a interface do retry.** As novas tentativas
  acontecem dentro do nó `tools` e não aparecem no `stream`; sem esse print o retry fica
  invisível. Não remova.
- **Variações são trocadas na tela pelo instrutor:** comentar o `ToolErrorMiddleware`,
  `FALHAS_SIMULADAS = 5` para esgotar as tentativas, `PermissionError` no lugar do
  `TimeoutError`, `ToolRetryMiddleware()` com os padrões. Não crie flag, `.env` nem modo.
- **Ordem da lista:** `ToolErrorMiddleware` primeiro (externo), `ToolRetryMiddleware` depois
  (interno) com `on_failure="error"`. Inverter quebra a lição.
- **Fora daqui:** retry do SDK, filtro `tools=` do retry, PII, human-in-the-loop e guardrail
  customizado.
- O log usa `agent.stream(..., stream_mode="updates")` e mostra o `status` do `ToolMessage`.
- **Provider:** chat Anthropic (`MODELO`, padrão `claude-haiku-5-5`). Sem `temperature`.
- Use `uv`.
