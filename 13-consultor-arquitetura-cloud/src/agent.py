"""Agente que combina histórico da thread com ferramentas de Store."""

import os

from langchain.agents import create_agent
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.base import BaseStore

from src.memory_tools import AgentContext, TOOLS

SYSTEM_PROMPT = """Você é um consultor didático de arquitetura Cloud. Responda em português brasileiro.
Ao começar uma conversa, pergunte se o usuário quer criar um projeto ou continuar um existente.
Se a primeira mensagem já responder a essa pergunta, execute o pedido sem repeti-la.
Se ele quiser consultar o catálogo, use listar_projetos. Não presuma um projeto ativo em uma thread nova.
Use o nome do projeto nas ferramentas. O Store separa o catálogo de projetos dos itens de decisão.
Antes de responder sobre decisões anteriores, chame consultar_projeto; não invente memórias.
Registre uma decisão somente quando o usuário disser explicitamente que a aceitou ou pedir para registrá-la.
Escolhas de provedor e região também são decisões quando o usuário as confirma.
Registre uma decisão por chamada da ferramenta, sem exigir justificativa ou motivo.
Uma alternativa proposta, hipótese ou recomendação ainda não é uma decisão.
Não grave chaves de API, tokens ou outros segredos no Store; explique esse limite ao usuário.
Os dados Cloud deste exemplo são declarados pelo usuário; não alegue ter consultado infraestrutura real.
"""


def respond(
    checkpointer: BaseCheckpointSaver,
    store: BaseStore,
    user_id: str,
    thread_id: str,
    prompt: str,
) -> None:
    """Envia uma mensagem ao agente com a thread e a identidade do usuário.

    Args:
        checkpointer: Persistência do histórico das mensagens por thread.
        store: Persistência dos projetos e decisões entre threads.
        user_id: Perfil selecionado na página, usado para isolar o Store.
        thread_id: Identificador da conversa que receberá a mensagem.
        prompt: Nova mensagem escrita pelo usuário.
    """
    agent = create_agent(
        model=f"anthropic:{os.getenv('MODELO', 'claude-sonnet-5')}",
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
        store=store,
        context_schema=AgentContext,
    )
    thread_config = {"configurable": {"thread_id": thread_id}}
    agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]},
        thread_config,
        context=AgentContext(user_id=user_id),
    )
