import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from src.ferramentas import FERRAMENTAS, MAQUINAS

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("Configure ANTHROPIC_API_KEY no arquivo .env antes de executar.")

SYSTEM_PROMPT = """
Você é o assistente de operação das máquinas do time. Consulte as máquinas com
listar_maquinas antes de agir. Só ligue, desligue ou reinicie quando o usuário pedir.
Para cada ação, faça uma única chamada com todas as máquinas na lista.
"""

DESTINO = {
    "ligar_maquinas": "active",
    "desligar_maquinas": "off",
    "reiniciar_maquinas": "reinício",
}


def previa(tool_call, state, runtime) -> str:
    """Monta o que vai mudar em cada máquina, sem executar nada."""
    linhas = [tool_call["name"]]
    for nome in tool_call["args"].get("nomes", []):
        maquina = MAQUINAS.get(nome)
        if maquina is None:
            linhas.append(f"{nome}: máquina não encontrada")
        else:
            linhas.append(
                f"{nome} ({maquina['ambiente']}, {maquina['papel']}) "
                f"{maquina['status']} => {DESTINO[tool_call['name']]}"
            )
    return "\n".join(linhas)


APROVACAO = HumanInTheLoopMiddleware(
    interrupt_on={
        "listar_maquinas": False,  # leitura: roda sem aprovação
        "ligar_maquinas": {
            "allowed_decisions": ["approve", "reject"],
            "description": previa,
        },
        "desligar_maquinas": {
            "allowed_decisions": ["approve", "edit", "reject"],
            "description": previa,
        },
        "reiniciar_maquinas": {
            "allowed_decisions": ["approve", "edit", "reject"],
            "description": previa,
        },
    },
)

model = ChatAnthropic(model=os.getenv("MODELO", "claude-haiku-5-5"))

agent = create_agent(
    model=model,
    tools=FERRAMENTAS,
    system_prompt=SYSTEM_PROMPT,
    middleware=[APROVACAO],
    checkpointer=InMemorySaver(),  # sem checkpointer, não há de onde retomar
)


def executar(pergunta: str, thread_id: str) -> dict:
    """Roda o agente até a resposta ou até a primeira pausa para aprovação."""
    config = {"configurable": {"thread_id": thread_id}}
    resultado = agent.invoke({"messages": [("human", pergunta)]}, config)
    return ler_resultado(resultado)


def retomar(decisoes: list[dict], thread_id: str) -> dict:
    """Retoma a mesma thread com uma decisão por chamada pausada, na mesma ordem."""
    config = {"configurable": {"thread_id": thread_id}}
    # O Command leva a decisão humana como dado, não como texto: uma decisão por chamada pausada.
    # Mesmo thread_id => a execução continua do ponto em que pausou.
    resultado = agent.invoke(Command(resume={"decisions": decisoes}), config)
    return ler_resultado(resultado)


def ler_resultado(resultado: dict) -> dict:
    """A pausa chega como dado: quem chamou decide como mostrar e devolve a decisão."""
    if resultado.get("__interrupt__"):
        pausa = resultado["__interrupt__"][0]
        return {"pausa": pausa.value, "pausa_id": pausa.id, "mensagens": resultado["messages"]}
    return {"resposta": resultado["messages"][-1].text, "mensagens": resultado["messages"]}
