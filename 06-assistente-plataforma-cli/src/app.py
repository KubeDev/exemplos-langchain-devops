import argparse
import asyncio
import os
import sys
from collections.abc import Sequence

from dotenv import load_dotenv

from src.observability import DidacticObservabilityCallback
from src.tools import ConfigurationError, mcp_config

SYSTEM_PROMPT = """
Você é um assistente de plataforma que consulta o estado do Kubernetes usando as ferramentas
disponíveis. Nunca altere recursos, consulte Secrets ou revele credenciais. Se uma informação não
estiver disponível, diga que não sabe.
"""


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="assistente-plataforma-cli",
        description="Consulta o Kubernetes em linguagem natural por meio de um agente.",
    )
    parser.add_argument("pergunta", help="solicitação em linguagem natural")
    parser.add_argument(
        "--namespace",
        help="namespace usado como contexto adicional da solicitação",
    )
    return parser


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

    from langchain.agents import create_agent
    from langchain.mcp import MCPAdapter
    from langchain_anthropic import ChatAnthropic

    model = ChatAnthropic(model=os.getenv("MODELO", "claude-sonnet-5"))
    solicitacao = compor_solicitacao(pergunta, namespace)
    observability = DidacticObservabilityCallback()
    observability.question_received(solicitacao)

    async with MCPAdapter(mcp_config()) as adapter:
        tools = await adapter.list_tools()
        print(
            f"[observabilidade] catálogo MCP descoberto: {len(tools)} ferramentas",
            file=sys.stderr,
            flush=True,
        )
        agent = create_agent(model=model, tools=tools, system_prompt=SYSTEM_PROMPT)
        resultado = await agent.ainvoke(
            {"messages": [("human", solicitacao)]},
            config={"callbacks": [observability]},
        )

    resposta = resultado["messages"][-1].text
    observability.final_answer(resposta)
    return resposta


def main(argv: Sequence[str] | None = None) -> None:
    args = criar_parser().parse_args(argv)

    try:
        resposta = asyncio.run(executar(args.pergunta, args.namespace))
    except ConfigurationError as error:
        print(f"Erro de configuração: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    except Exception as error:
        print(f"Falha durante a execução: {type(error).__name__}", file=sys.stderr)
        raise SystemExit(1) from error

    print(resposta)


if __name__ == "__main__":
    main()
