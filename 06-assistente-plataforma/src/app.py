import asyncio
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.mcp import MCPAdapter
from langchain_anthropic import ChatAnthropic

from src.tools import MCP_CONFIG

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("Configure ANTHROPIC_API_KEY no arquivo .env antes de executar.")

SYSTEM_PROMPT = """
Você é um assistente de plataforma que consulta o estado do Kubernetes usando as ferramentas
disponíveis. Nunca altere recursos, consulte Secrets ou revele credenciais. Se uma informação não
estiver disponível, diga que não sabe.
"""


async def executar() -> None:
    model = ChatAnthropic(model=os.getenv("MODELO", "claude-sonnet-5"))

    async with MCPAdapter(MCP_CONFIG) as adapter:
        tools = await adapter.list_tools()

        print("Ferramentas MCP disponíveis:")
        for tool in tools:
            print(f"- {tool.name}")

        agent = create_agent(model=model, tools=tools, system_prompt=SYSTEM_PROMPT)

        pergunta = input("\nPergunta: ")

        resultado = await agent.ainvoke({"messages": [("human", pergunta)]})
        resposta = resultado["messages"][-1].text

        print("Resposta:")
        print(resposta)


def main() -> None:
    asyncio.run(executar())


if __name__ == "__main__":
    main()
