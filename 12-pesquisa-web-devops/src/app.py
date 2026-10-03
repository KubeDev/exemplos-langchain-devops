import argparse
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_firecrawl import FirecrawlScrape
from langchain_tavily import TavilySearch

load_dotenv()

for chave in ("ANTHROPIC_API_KEY", "TAVILY_API_KEY", "FIRECRAWL_API_KEY"):
    if not os.getenv(chave):
        raise SystemExit(f"Configure {chave} no arquivo .env antes de executar.")

SYSTEM_PROMPT = """
Você é um assistente de pesquisa sobre DevOps e cloud.
Use a ferramenta disponível para responder e cite as fontes que consultou.
"""

# As duas ferramentas prontas, cada uma do seu pacote.
busca = TavilySearch(max_results=5)
leitura = FirecrawlScrape()

model = ChatAnthropic(model=os.getenv("MODELO", "claude-sonnet-5"))

agent = create_agent(
    model=model,
    # Troque a ferramenta: busca · leitura
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
    for mensagem in resultado["messages"]:
        for chamada in getattr(mensagem, "tool_calls", []):
            print(f"Ferramenta: {chamada['name']}({chamada['args']})")

    print("\nResposta:")
    print(resultado["messages"][-1].text)


if __name__ == "__main__":
    main()
