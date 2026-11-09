# Contexto deste exemplo

Leia o `README.md` e o `CLAUDE.md` da raiz do repositório antes de alterar o projeto.

Exemplo `26` da série, a aula "Handoff e Transferência de Controle por Estado". A lição é **a transferência de
controle por estado**: a ferramenta de transferência escreve o `agente_ativo` com `Command`, e um middleware lê o campo
e troca a identidade do agente. Com o campo vazio, atende a triagem.

- **Autocontido.** Não importa nada de outro exemplo, nem copia dados de outro exemplo. Os dados são simulados em
  `src/ferramentas.py`.
- **`src/agente.py` é o arquivo lido em aula, de cima a baixo:** estado, ferramentas de transferência, `IDENTIDADES`,
  middleware `trocar_identidade`, `create_agent` e `responder`.
  Mantenha essa ordem. `ferramentas.py` e `web.py` são encanamento, só apontados.
- **Um agente com middleware, não subgrafos.** A forma com subgrafos e `Command.PARENT` é só citada. Não monte grafo,
  `StateGraph` nem `Send`.
- **O `create_agent` recebe a união das ferramentas.** O middleware filtra com `request.override(tools=...)`; ferramenta
  que não está no `create_agent` dá `ValueError` (conferido em langchain 1.4.9).
- **`system_message=SystemMessage(...)` no `override`**, não `system_prompt`, que está deprecado.
- **Sem roteador.** O roteador foi ensinado antes, como workflow de routing; aqui ele não entra. A primeira mensagem
  é atendida pela identidade `triagem` (padrão quando `agente_ativo` está vazio), que só tem as duas ferramentas de
  transferência e, fora do escopo, responde sem transferir.
- **A `ToolMessage` diz de quem para quem**, lendo `runtime.state`, porque a mesma ferramenta pode vir da triagem ou de
  um especialista.
- **Modelo padrão `claude-sonnet-5-5`.** Com Haiku, o especialista que recebe a transferência às vezes toma as
  respostas e a chamada de transferência do anterior como dele e "se corrige". Sem `temperature`.
- **O que acompanha a transferência é o histórico inteiro.** A `ToolMessage` diz de quem para quem, e cada prompt
  avisa que as respostas anteriores podem ser de outro especialista. Não recorte mensagens no middleware: o recorte é
  assunto da forma com subgrafos, só citado na aula.
- **Os especialistas transferem um para o outro.** Capacidade não estima custo; FinOps não projeta capacidade.
- **Os prompts forçam a pergunta ao usuário** (multiplicador de tráfego; se o recurso ocioso foi planejado). É o que
  prova que o especialista conduz a conversa. Não remova.
- **`web.py`:** o agente vive no módulo importado, então o `InMemorySaver` sobrevive aos reruns do Streamlit sem
  `st.cache_resource`. O rótulo de cada resposta é derivado das `ToolMessage` de transferência.
- **Fora daqui:** roteador, subgrafos, recorte de contexto, skills, subagente, grafo/LangGraph, persistência em banco.
- Use `uv`.
