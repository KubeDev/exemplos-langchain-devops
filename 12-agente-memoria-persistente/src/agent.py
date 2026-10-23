"""Chamada do agente com a mensagem nova e a thread escolhida."""

import os

from langchain.agents import create_agent
from langgraph.checkpoint.base import BaseCheckpointSaver

SYSTEM_PROMPT = "Você é um assistente de uso geral. Responda em português brasileiro, de forma clara e concisa."


def respond(checkpointer: BaseCheckpointSaver, thread_id: str, prompt: str) -> None:
    """Envia apenas a nova mensagem ao agente na thread informada."""

    agent = create_agent(
        model=f"anthropic:{os.getenv('MODELO', 'claude-sonnet-5')}",
        tools=[],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
    thread_config = {"configurable": {"thread_id": thread_id}}
    agent.invoke({"messages": [{"role": "user", "content": prompt}]}, thread_config)
