import argparse
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware
from langchain.messages import AIMessage, ToolMessage
from langchain.tools import tool
from langchain_anthropic import ChatAnthropic

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("Configure ANTHROPIC_API_KEY no arquivo .env antes de executar.")

PERGUNTA = "O deploy {deploy_id} já terminou?"

SYSTEM_PROMPT = """
Você acompanha deploys da plataforma. Use a ferramenta consultar_status_deploy para saber
o status de um deploy. Só responda ao usuário quando o deploy terminar, com status
concluido ou falhou.
"""


@tool
def consultar_status_deploy(deploy_id: str) -> str:
    """Consulta o status atual de um deploy da plataforma.

    Args:
        deploy_id: Identificador do deploy, como dpl-4821.
    """
    return f"deploy {deploy_id}: status provisioning"


model = ChatAnthropic(model=os.getenv("MODELO", "claude-haiku-5-5"))

agent = create_agent(
    model=model,
    tools=[consultar_status_deploy],
    system_prompt=SYSTEM_PROMPT,
    middleware=[
        ToolCallLimitMiddleware(tool_name="consultar_status_deploy", run_limit=3),
    ],
)


def mostrar(etapa: str, mensagem) -> None:
    if isinstance(mensagem, AIMessage) and mensagem.tool_calls:
        for chamada in mensagem.tool_calls:
            print(f"[{etapa}] chama {chamada['name']}({chamada['args']})")
    elif isinstance(mensagem, ToolMessage):
        print(f"[{etapa}] devolve: {mensagem.content}")
    else:
        print(f"[{etapa}] responde: {mensagem.text}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Acompanha um deploy com limite de chamadas de ferramenta."
    )
    parser.add_argument("deploy_id", help="Ex.: dpl-4821")
    args = parser.parse_args()

    pergunta = PERGUNTA.format(deploy_id=args.deploy_id)
    print(f"Pergunta: {pergunta}\n")

    for passo in agent.stream({"messages": [("human", pergunta)]}, stream_mode="updates"):
        for etapa, atualizacao in passo.items():
            for mensagem in (atualizacao or {}).get("messages", []):
                mostrar(etapa, mensagem)


if __name__ == "__main__":
    main()
