import asyncio
import os
import sys
from typing import Annotated

import typer
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain.mcp import MCPAdapter
from langchain_anthropic import ChatAnthropic

from src.tools import ConfigurationError, mcp_config

SYSTEM_PROMPT = """
Você é um assistente de plataforma que consulta o estado do Kubernetes usando as ferramentas
disponíveis. Nunca altere recursos, consulte Secrets ou revele credenciais. Se uma informação não
estiver disponível, diga que não sabe.
"""


def compor_solicitacao(pergunta: str, namespace: str | None) -> str:
    if namespace:
        return f"{pergunta}\nContexto adicional: namespace Kubernetes {namespace}."
    return pergunta


async def executar(pergunta: str, namespace: str | None = None) -> str:
    load_dotenv()

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise ConfigurationError(
            "Configure ANTHROPIC_API_KEY no arquivo .env antes de executar."
        )

    model = ChatAnthropic(model=os.getenv("MODELO", "claude-sonnet-5"))
    solicitacao = compor_solicitacao(pergunta, namespace)

    async with MCPAdapter(mcp_config()) as adapter:
        tools = await adapter.list_tools()
        print(f"Catálogo MCP: {len(tools)} ferramentas", file=sys.stderr, flush=True)
        agent = create_agent(model=model, tools=tools, system_prompt=SYSTEM_PROMPT)
        resultado = await agent.ainvoke({"messages": [("human", solicitacao)]})

    return resultado["messages"][-1].text


app = typer.Typer(add_completion=False)


@app.command()
def main(
    pergunta: Annotated[str, typer.Argument(help="solicitação em linguagem natural")],
    namespace: Annotated[
        str | None,
        typer.Option(help="namespace usado como contexto adicional da solicitação"),
    ] = None,
) -> None:
    """Consulta o Kubernetes em linguagem natural por meio de um agente."""
    try:
        resposta = asyncio.run(executar(pergunta, namespace))
    except ConfigurationError as error:
        print(f"Erro de configuração: {error}", file=sys.stderr)
        raise typer.Exit(1) from error
    except Exception as error:
        print(f"Falha durante a execução: {type(error).__name__}", file=sys.stderr)
        raise typer.Exit(1) from error

    print(resposta)


if __name__ == "__main__":
    app()
