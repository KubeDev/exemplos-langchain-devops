import os
from typing import Literal, NotRequired

from dotenv import load_dotenv
from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import ModelRequest, ModelResponse, wrap_model_call
from langchain.messages import HumanMessage, SystemMessage, ToolMessage
from langchain.tools import ToolRuntime, tool
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from src.ferramentas import FERRAMENTAS_CAPACIDADE, FERRAMENTAS_FINOPS

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("Configure ANTHROPIC_API_KEY no arquivo .env antes de executar.")

model = ChatAnthropic(model=os.getenv("MODELO", "claude-sonnet-5-5"))

# ---------------------------------------------------------------------------
# 1. Estado: quem está atendendo
# ---------------------------------------------------------------------------


class EstadoCentral(AgentState):
    agente_ativo: NotRequired[Literal["triagem", "finops", "capacidade"]]


# ---------------------------------------------------------------------------
# 2. Ferramentas de transferência (handoff)
# ---------------------------------------------------------------------------

NOMES = {"triagem": "Triagem", "finops": "FinOps", "capacidade": "Capacidade"}


def transferir(destino: str, runtime: ToolRuntime) -> Command:
    """Grava o destino no estado e responde à chamada dizendo de quem para quem."""
    origem = NOMES[runtime.state.get("agente_ativo", "triagem")]
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"Conversa transferida de {origem} para {NOMES[destino]}. "
                    f"As respostas anteriores foram de {origem}.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
            "agente_ativo": destino,
        }
    )


@tool
def transferir_para_finops(runtime: ToolRuntime) -> Command:
    """Transfere a conversa para o especialista de FinOps. Use quando o assunto for custo:
    quanto se gastou, por que a conta subiu ou quanto algo vai custar."""
    return transferir("finops", runtime)


@tool
def transferir_para_capacidade(runtime: ToolRuntime) -> Command:
    """Transfere a conversa para o especialista de Capacidade. Use quando o assunto for se a
    aplicação aguenta um aumento de tráfego, quantas réplicas precisa ou onde está o gargalo."""
    return transferir("capacidade", runtime)


# ---------------------------------------------------------------------------
# 3. Identidades: o prompt e as ferramentas de cada especialista
# ---------------------------------------------------------------------------

IDENTIDADES = {
    "triagem": {
        "prompt": """
Você é a triagem da central da plataforma cloud. A central tem dois especialistas: FinOps
(custo: quanto se gastou, por que a conta subiu, desperdício, quanto algo vai custar) e
Capacidade (se a aplicação aguenta tráfego, réplicas, gargalo). Você não responde o mérito:
identifique o assunto e transfira para o especialista. Se não der para saber o assunto, faça
uma pergunta curta ao usuário. Se o assunto não for de nenhum dos dois, diga que a central
atende custo e capacidade da plataforma e não transfira.
""",
        "ferramentas": [transferir_para_finops, transferir_para_capacidade],
    },
    "finops": {
        "prompt": """
Você é o especialista de FinOps da central da plataforma cloud. Você olha para o que já foi
gasto: custo por serviço, aumento da conta e desperdício. Quando a conta subir, consulte os
recursos ociosos e, antes de recomendar desligar algo, pergunte ao usuário se aquele recurso
foi planejado e se ainda está em uso. Faça uma pergunta por vez. Se o assunto mudar para
capacidade (aguentar tráfego, réplicas, gargalo), transfira para Capacidade.
A conversa pode ter começado na triagem ou com outro especialista: as respostas e as chamadas
de ferramenta anteriores à transferência foram deles, não suas. Use o que já foi apurado sem corrigir.
""",
        "ferramentas": [*FERRAMENTAS_FINOPS, transferir_para_capacidade],
    },
    "capacidade": {
        "prompt": """
Você é o especialista de Capacidade da central da plataforma cloud. Você olha para frente: se
a aplicação aguenta um aumento de tráfego e onde está o gargalo. Antes de projetar, pergunte ao
usuário quanto tráfego ele espera em relação ao atual (por exemplo, 2x ou 3x). Faça uma
pergunta por vez. Você não estima custo: se o usuário perguntar quanto vai custar, transfira
para FinOps.
A conversa pode ter começado na triagem ou com outro especialista: as respostas e as chamadas
de ferramenta anteriores à transferência foram deles, não suas. Use o que já foi apurado sem corrigir.
""",
        "ferramentas": [*FERRAMENTAS_CAPACIDADE, transferir_para_finops],
    },
}

# ---------------------------------------------------------------------------
# 4. Middleware: troca a identidade a cada chamada de modelo, pelo estado
# ---------------------------------------------------------------------------


@wrap_model_call
def trocar_identidade(request: ModelRequest, handler) -> ModelResponse:
    identidade = IDENTIDADES[request.state.get("agente_ativo", "triagem")]
    return handler(
        request.override(
            system_message=SystemMessage(content=identidade["prompt"]),
            tools=identidade["ferramentas"],
        )
    )


# ---------------------------------------------------------------------------
# 5. O agente: todas as ferramentas registradas, o middleware escolhe quais o modelo vê
# ---------------------------------------------------------------------------

agent = create_agent(
    model=model,
    tools=[*FERRAMENTAS_FINOPS, *FERRAMENTAS_CAPACIDADE, transferir_para_finops, transferir_para_capacidade],
    state_schema=EstadoCentral,
    middleware=[trocar_identidade],
    checkpointer=InMemorySaver(),
)


def responder(pergunta: str, thread_id: str) -> dict:
    """Um turno da conversa. Sem agente_ativo no estado, quem atende é a triagem."""
    config = {"configurable": {"thread_id": thread_id}}
    antes = agent.get_state(config).values
    resultado = agent.invoke({"messages": [HumanMessage(content=pergunta)]}, config)
    return {
        "agente_inicial": antes.get("agente_ativo", "triagem"),
        "agente_ativo": resultado.get("agente_ativo", "triagem"),
        "mensagens": resultado["messages"][len(antes.get("messages", [])) :],
    }
