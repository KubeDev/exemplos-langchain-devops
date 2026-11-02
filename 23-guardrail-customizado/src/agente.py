import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import InMemorySaver

from src.ferramentas import FERRAMENTAS
from src.guardrail import GuardrailManutencao

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("Configure ANTHROPIC_API_KEY no arquivo .env antes de executar.")

SYSTEM_PROMPT = """
Você é o assistente de operação das máquinas do time. Consulte as máquinas com
listar_maquinas antes de agir. Só desligue quando o usuário pedir, numa única chamada
com todas as máquinas na lista.
"""

APROVACAO = HumanInTheLoopMiddleware(
    interrupt_on={
        "listar_maquinas": False,
        "desligar_maquinas": {"allowed_decisions": ["approve", "reject"]},
    },
)

GUARDRAIL = GuardrailManutencao(
    tag="prod",
    arquivo=os.getenv("ARQUIVO_MANUTENCAO", "manutencao.txt"),
)

model = ChatAnthropic(model=os.getenv("MODELO", "claude-haiku-5-5"))

agent = create_agent(
    model=model,
    tools=FERRAMENTAS,
    system_prompt=SYSTEM_PROMPT,
    middleware=[APROVACAO, GUARDRAIL],
    checkpointer=InMemorySaver(),
)
