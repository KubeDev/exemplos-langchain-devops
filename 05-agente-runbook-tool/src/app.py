import argparse
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic

from src.tools import consultar_runbook

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("Configure ANTHROPIC_API_KEY no arquivo .env antes de executar.")

PERGUNTA = "Analise o runbook {runbook_id}, de um resumo em 1 parágrafo."

SYSTEM_PROMPT = """
Você é um agente de operações responsável por orientar a resposta a incidentes.
Quando a pergunta mencionar um runbook interno, use a ferramenta consultar_runbook
com o identificador informado. Responda somente com o procedimento retornado pela ferramenta.
"""

model = ChatAnthropic(model=os.getenv("MODELO", "claude-sonnet-5"))

agent = create_agent(
    model=model,
    tools=[consultar_runbook],
    system_prompt=SYSTEM_PROMPT,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consulta runbooks internos usando um agente com ferramenta."
    )
    parser.add_argument("runbook_id")
    args = parser.parse_args()

    pergunta = PERGUNTA.format(runbook_id=args.runbook_id)
    print(f"Pergunta: {pergunta}\n")

    resultado = agent.invoke({"messages": [("human", pergunta)]})

    print("\nResposta:")
    print(resultado["messages"][-1].text)


if __name__ == "__main__":
    main()
