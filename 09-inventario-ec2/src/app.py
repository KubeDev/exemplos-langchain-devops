import argparse
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic

# Troque o módulo para mudar a forma da ferramenta:
# docstring_sem_parse · docstring · anotada · modelo_pydantic
from src.ferramentas.modelo_pydantic import listar_instancias

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("Configure ANTHROPIC_API_KEY no arquivo .env antes de executar.")

SYSTEM_PROMPT = """
Você é um assistente de operações que consulta o inventário de instâncias EC2 da conta.
Use a ferramenta listar_instancias para responder e não invente instâncias.
Você é especialista em AWS.
"""

model = ChatAnthropic(model=os.getenv("MODELO", "claude-sonnet-5"))

agent = create_agent(
    model=model,
    tools=[listar_instancias],
    system_prompt=SYSTEM_PROMPT,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consulta o inventário EC2 usando um agente com ferramenta."
    )
    parser.add_argument("pergunta")
    args = parser.parse_args()

    print(f"Pergunta: {args.pergunta}\n")

    resultado = agent.invoke({"messages": [("human", args.pergunta)]})

    print("\nResposta:")
    print(resultado["messages"][-1].text)


if __name__ == "__main__":
    main()
