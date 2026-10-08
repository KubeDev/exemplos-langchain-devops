import argparse
import os
from datetime import date

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_tavily import TavilySearch

load_dotenv()

for chave in ("ANTHROPIC_API_KEY", "TAVILY_API_KEY"):
    if not os.getenv(chave):
        raise SystemExit(f"Configure {chave} no arquivo .env antes de executar.")

SYSTEM_PROMPT = f"""
Você é um assistente de pesquisa sobre DevOps e cloud.
A data de hoje é {date.today().isoformat()}.
Use a ferramenta disponível para responder e cite as fontes que consultou.
"""

# A ferramenta pronta: vem do pacote e usa a TAVILY_API_KEY.
busca = TavilySearch(max_results=5)

model = ChatAnthropic(model=os.getenv("MODELO", "claude-sonnet-5"))

agent = create_agent(
    model=model,
    tools=[busca],
    system_prompt=SYSTEM_PROMPT,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pesquisa sobre DevOps e cloud usando uma ferramenta pronta."
    )
    parser.add_argument("pergunta")
    args = parser.parse_args()

    print(f"Pergunta: {args.pergunta}\n")

    resultado = agent.invoke({"messages": [("human", args.pergunta)]})

    # A ferramenta pronta não tem corpo nosso para imprimir a chamada:
    # a chamada pedida pelo modelo é lida das mensagens.
    # Esses argumentos são o que sai do seu ambiente e vai para o Tavily.
    for mensagem in resultado["messages"]:
        for chamada in getattr(mensagem, "tool_calls", []):
            print(f"Ferramenta: {chamada['name']}({chamada['args']})")

    print("\nResposta:")
    print(resultado["messages"][-1].text)


if __name__ == "__main__":
    main()
