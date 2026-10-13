import argparse
import asyncio
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.mcp import MCPAdapter
from langchain_anthropic import ChatAnthropic

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("Configure ANTHROPIC_API_KEY no arquivo .env antes de executar.")

MCP_CONFIG = {
    "mcpServers": {
        "digitalocean": {
            "transport": "http",
            "url": os.getenv("MCP_URL", "http://localhost:8000/mcp"),
        }
    }
}

SYSTEM_PROMPT = """
Você é um assistente de operações que consulta a conta DigitalOcean usando as ferramentas
disponíveis. Não invente recursos. Só ligue ou desligue um Droplet quando o usuário pedir
explicitamente.
Você é especialista em DigitalOcean.
"""


async def executar(pergunta: str) -> None:
    model = ChatAnthropic(model=os.getenv("MODELO", "claude-sonnet-5"))

    async with MCPAdapter(MCP_CONFIG) as adapter:
        tools = await adapter.list_tools()

        print("Ferramentas MCP disponíveis:")
        for tool in tools:
            print(f"- {tool.name}")

        agent = create_agent(model=model, tools=tools, system_prompt=SYSTEM_PROMPT)

        print(f"\nPergunta: {pergunta}\n")

        resultado = await agent.ainvoke({"messages": [("human", pergunta)]})

        print("Resposta:")
        print(resultado["messages"][-1].text)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consulta a conta DigitalOcean usando as ferramentas de um MCP server."
    )
    parser.add_argument("pergunta", help="Ex.: \"Quais Droplets estão ativos?\"")
    args = parser.parse_args()

    asyncio.run(executar(args.pergunta))


if __name__ == "__main__":
    main()
