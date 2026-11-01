# Contexto deste exemplo

Leia o `README.md` e o `CLAUDE.md` da raiz do repositório antes de alterar o projeto.

Exemplo `22` da série. A lição é: **human-in-the-loop em ações de escrita**. O
`HumanInTheLoopMiddleware` pausa toda chamada que liga, desliga ou reinicia uma máquina,
mostra uma prévia legível e retoma a mesma thread com a decisão (`approve`, `edit`, `reject`).

- **Três arquivos, um papel cada.** `ferramentas.py` (máquinas em memória + ferramentas),
  `agente.py` (o arquivo lido em aula: middleware, `previa`, checkpointer, `executar`/`retomar`)
  e `web.py` (só Streamlit, apontado em aula). Nada de Streamlit no `agente.py`: a separação é
  o argumento de que a pausa é dado e qualquer interface a lê.
- **As máquinas são simuladas e ficam em memória.** Sem MCP, sem API real, sem arquivo de estado.
  Reiniciar o servidor é o reset do cenário.
- **Escrita recebe lista de nomes.** É o que dá ao `edit` um ajuste pequeno (tirar uma máquina).
  As docstrings e o system prompt pedem uma chamada por ação com todas as máquinas.
- **`ligar_maquinas` não aceita `edit`** de propósito: mostra `allowed_decisions` por ferramenta.
- **`listar_maquinas` entra no `interrupt_on` com `False`**: leitura roda sem aprovação, mas fica declarada no mapa. Ferramenta fora do mapa teria o mesmo efeito; o `False` deixa a escolha visível.
- **O system prompt não pede confirmação.** O freio é o middleware; "só aja quando o usuário
  pedir" fica lá para mostrar que o prompt não garante.
- **Pedido da demo de `edit`: "Desliga todas as máquinas ligadas".** Sem o "todas", o modelo às
  vezes deixa a `api-01` de fora ou pede confirmação sozinho (verificado em 01/11/2026).
- **Variações trocadas na tela pelo instrutor:** comentar `middleware=[APROVACAO]`; comentar as
  linhas `"description": previa` para ver a descrição padrão. Não crie flag nem modo.
- **Fora daqui:** guardrail customizado, PII, `per_call` (só nomeado), `respond`, checkpointer
  persistente, autenticação e auditoria.
- **Provider:** chat Anthropic (`MODELO`, padrão `claude-haiku-5-5`). Sem `temperature`.
- Use `uv`.
