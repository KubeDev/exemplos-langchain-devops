import argparse
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic

# Troque o módulo para mudar a forma da ferramenta: docstring · modelo_pydantic
from src.ferramentas.docstring import listar_droplets

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("Configure ANTHROPIC_API_KEY no arquivo .env antes de executar.")
if not os.getenv("DIGITALOCEAN_TOKEN"):
    raise SystemExit("Configure DIGITALOCEAN_TOKEN no arquivo .env antes de executar.")

SYSTEM_PROMPT = """
Você é um assistente de operações que consulta o inventário de Droplets da conta DigitalOcean.
Use a ferramenta listar_droplets para responder e não invente Droplets.
Você é especialista em DigitalOcean.
"""

model = ChatAnthropic(model=os.getenv("MODELO", "claude-sonnet-5"))

agent = create_agent(
    model=model,
    tools=[listar_droplets],
    system_prompt=SYSTEM_PROMPT,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consulta o inventário de Droplets usando um agente com ferramenta."
    )
    parser.add_argument("pergunta", help="Ex.: \"Quais Droplets ativos têm pelo menos 2 GB de memória?\"")
    args = parser.parse_args()

    print(f"Pergunta: {args.pergunta}\n")

    resultado = agent.invoke({"messages": [("human", args.pergunta)]})

    print("\nResposta:")
    print(resultado["messages"][-1].text)


if __name__ == "__main__":
    main()
