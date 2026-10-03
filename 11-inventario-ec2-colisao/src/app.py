import argparse
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic

# Troque o módulo para mudar as descrições das ferramentas:
# ambiguas · contrastivas
from src.ferramentas.ambiguas import listar_instancias, verificar_status

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("Configure ANTHROPIC_API_KEY no arquivo .env antes de executar.")

SYSTEM_PROMPT = """
Você é um assistente de operações que consulta as instâncias EC2 da conta.
Use as ferramentas para responder e não invente instâncias.
Você é especialista em AWS.
"""

model = ChatAnthropic(model=os.getenv("MODELO", "claude-sonnet-5"))

agent = create_agent(
    model=model,
    tools=[listar_instancias, verificar_status],
    system_prompt=SYSTEM_PROMPT,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consulta as instâncias EC2 usando um agente com duas ferramentas."
    )
    parser.add_argument("pergunta")
    args = parser.parse_args()

    print(f"Pergunta: {args.pergunta}\n")

    resultado = agent.invoke({"messages": [("human", args.pergunta)]})

    print("\nResposta:")
    print(resultado["messages"][-1].text)


if __name__ == "__main__":
    main()
