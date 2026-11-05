# Contexto deste exemplo

Leia o `README.md` e o `CLAUDE.md` da raiz do repositório antes de alterar o projeto.

Exemplo `23` da série. A lição é: **criar o seu próprio middleware**. Uma regra do time
(máquina do ambiente `prod` só desliga com a janela de manutenção aberta) vira a classe
`GuardrailManutencao`, um hook tipo wrap que barra a chamada de ferramenta por curto-circuito.

- **O `23` é o `22` mais o guardrail.** `src/ferramentas.py` e `src/web.py` são cópias idênticas
  dos do `22`; o `src/agente.py` só difere pelo import, pelo bloco `GUARDRAIL` e pela lista de
  middlewares. É o que deixa a diferença entre as aulas visível num `diff -r`. Mudança no `22`
  nesses arquivos deve ser replicada aqui; não acrescente nada ao `23` que não seja o guardrail.
- **`src/guardrail.py` é o arquivo lido em aula.** Três peças, nessa ordem: `janela_aberta`
  (lê a flag), `verificar` (a regra pura, devolve o motivo ou `None`) e a classe. Não junte a
  regra dentro do `wrap_tool_call`: a função pura é o que o teste exercita.
- **A regra é por `ambiente` e só para `desligar_maquinas`.** Ligar e reiniciar passam.
- **Classe, não decorador.** A classe recebe `ambiente` e `arquivo` no `__init__` e entra na
  lista com a mesma cara dos middlewares prontos. Não troque por `@wrap_tool_call`.
- **A flag é lida a cada chamada**, dentro do `wrap_tool_call`, nunca no `__init__`: é o que
  deixa o instrutor abrir e fechar a janela sem reiniciar o servidor.
- **Arquivo inacessível = janela fechada.** O `try/except` em `janela_aberta` é só isso; não
  vira tópico, não ganha teste com arquivo temporário.
- **Só dois middlewares: `HumanInTheLoopMiddleware` e o guardrail.** O HITL é o do `22` e existe
  para mostrar que a aprovação não passa por cima da regra: no modo `batched` ele pausa no
  `after_model`, e o guardrail roda depois, no nó `tools`. Não adicione `PIIMiddleware`.
- **Sem abstração para trocar a fonte da flag.** Banco ou serviço de configuração é só citado.
- **Testes sem arquivo temporário e sem chave de API:** só `verificar` com booleanos.
- **Fora daqui:** ordem entre vários guardrails, detector de injeção, guardrail baseado em modelo,
  `jump_to`, estado próprio do middleware.
- **Provider:** chat Anthropic (`MODELO`, padrão `claude-haiku-5-5`). Sem `temperature`.
- Use `uv`.
