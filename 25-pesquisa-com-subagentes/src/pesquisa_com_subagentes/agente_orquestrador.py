"""O agente orquestrador: delega aos dois subagentes e junta o que eles devolvem.

Ele não importa a busca na web nem o banco vetorial: só as duas ferramentas que embrulham os
subagentes. É o único agente que fala com o usuário e o único que tem memória da conversa.
"""

from langchain.agents import create_agent
from langgraph.checkpoint.base import BaseCheckpointSaver

from pesquisa_com_subagentes.ferramenta_subagente_docs import subagente_docs
from pesquisa_com_subagentes.ferramenta_subagente_web import subagente_web

MODELO = "claude-sonnet-5-5"

SYSTEM_PROMPT = """Você é o assistente de pesquisa do time. Responda em português brasileiro, de forma direta.
Você não pesquisa: delega aos subagentes e junta o que eles devolvem.
O que é dos projetos do time (kube-news e encontros-tech) vem do subagente_docs. O que é público vem do subagente_web.
Quando a pergunta precisa das duas fontes, chame os dois subagentes de uma vez.
Os subagentes não veem esta conversa: escreva em cada pedido tudo de que ele precisa.
Quando a pergunta depende do projeto e ele não foi dito, pergunte ao usuário antes de delegar.
Se o projeto já foi dito nesta conversa, use o mesmo sem perguntar de novo.
Cite as fontes que os subagentes devolveram."""


def responder(pergunta: str, thread_id: str, checkpointer: BaseCheckpointSaver) -> None:
    """Entrega a pergunta ao orquestrador, na thread da sessão."""
    orquestrador = create_agent(
        model=f"anthropic:{MODELO}",
        system_prompt=SYSTEM_PROMPT,
        tools=[subagente_web, subagente_docs],
        checkpointer=checkpointer,
    )
    orquestrador.invoke(
        {"messages": [{"role": "user", "content": pergunta}]},
        {"configurable": {"thread_id": thread_id}},
    )
