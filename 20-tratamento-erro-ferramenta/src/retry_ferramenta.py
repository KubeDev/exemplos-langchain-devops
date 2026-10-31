import argparse
import os
from datetime import datetime

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import ToolErrorMiddleware, ToolRetryMiddleware
from langchain.messages import AIMessage, ToolMessage
from langchain.tools import tool
from langchain_anthropic import ChatAnthropic

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("Configure ANTHROPIC_API_KEY no arquivo .env antes de executar.")

PERGUNTA = "Desligue o droplet {droplet_id}."

SYSTEM_PROMPT = """
Você opera Droplets da DigitalOcean. Use a ferramenta desligar_droplet para desligar um
Droplet pelo identificador e informe ao usuário o resultado.
"""

# Quantas chamadas à API falham antes de ela responder.
FALHAS_SIMULADAS = 1

chamadas = 0


@tool
def desligar_droplet(droplet_id: str) -> str:
    """Desliga um Droplet da DigitalOcean. Se ele já estiver desligado, não faz nada.

    Args:
        droplet_id: Identificador numérico do Droplet, como 498123456.
    """
    global chamadas
    chamadas += 1
    agora = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[api {agora}] chamada {chamadas} à DigitalOcean")

    # Simula a API instável: as primeiras chamadas estouram o tempo.
    if chamadas <= FALHAS_SIMULADAS:
        raise TimeoutError("DigitalOcean API: sem resposta em 10s")
    return f"droplet {droplet_id}: desligado"


def tratar_erro(erro: Exception, request) -> str | None:
    if isinstance(erro, PermissionError):
        return (
            "Falha de autenticação na DigitalOcean (PermissionError). Não tente de novo: "
            "peça ao usuário para verificar o token."
        )
    if isinstance(erro, TimeoutError):
        return (
            "A DigitalOcean não respondeu depois das novas tentativas (TimeoutError). "
            "Informe o usuário que a API está indisponível."
        )
    return None


model = ChatAnthropic(model=os.getenv("MODELO", "claude-haiku-5-5"))

agent = create_agent(
    model=model,
    tools=[desligar_droplet],
    system_prompt=SYSTEM_PROMPT,
    middleware=[
        ToolErrorMiddleware(tratar_erro),
        ToolRetryMiddleware(
            max_retries=2,
            backoff_factor=2.0,
            initial_delay=1.0,
            retry_on=(TimeoutError, ConnectionError),
            on_failure="error",
        ),
    ],
)


def mostrar(etapa: str, mensagem) -> None:
    if isinstance(mensagem, AIMessage) and mensagem.tool_calls:
        for chamada in mensagem.tool_calls:
            print(f"[{etapa}] chama {chamada['name']}({chamada['args']})")
    elif isinstance(mensagem, ToolMessage):
        print(f"[{etapa}] devolve ({mensagem.status}): {mensagem.content}")
    else:
        print(f"[{etapa}] responde: {mensagem.text}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Desliga um Droplet com nova tentativa e erro devolvido ao modelo."
    )
    parser.add_argument("droplet_id", help="Ex.: 498123456")
    args = parser.parse_args()

    pergunta = PERGUNTA.format(droplet_id=args.droplet_id)
    print(f"Pergunta: {pergunta}\n")

    for passo in agent.stream({"messages": [("human", pergunta)]}, stream_mode="updates"):
        for etapa, atualizacao in passo.items():
            for mensagem in (atualizacao or {}).get("messages", []):
                mostrar(etapa, mensagem)


if __name__ == "__main__":
    main()
