import os
import sys
import argparse
import warnings

from dotenv import load_dotenv

load_dotenv()

# O langgraph emite um aviso de depreciacao no import que aparece no topo da
# tela. Nao afeta o funcionamento e polui a aula -- silenciado de proposito,
# antes dos imports que o disparam.
warnings.filterwarnings("ignore", message=".*allowed_objects.*")

from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent
from langchain.messages import AIMessage, ToolMessage

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown

from src.tools import get_tools
from src.prompt import SYSTEM_PROMPT
from src.logs import definir_raiz, log_chamada, log_retorno

console = Console()

BANNER = r"""
 ____                       _   ____             _
/ ___| _ __ ___   __ _ _ __| |_|  _ \  ___   ___| | _____ _ __
\___ \| '_ ` _ \ / _` | '__| __| | | |/ _ \ / __| |/ / _ \ '__|
 ___) | | | | | | (_| | |  | |_| |_| | (_) | (__|   <  __/ |
|____/|_| |_| |_|\__,_|_|   \__|____/ \___/ \___|_|\_\___|_|
"""


def show_banner():
    banner_text = Text(BANNER, style="bold cyan")
    subtitle = Text("Analise inteligente de Dockerfiles", style="italic white")
    banner_text.append("\n")
    banner_text.append(subtitle)
    console.print(Panel(banner_text, border_style="cyan"))


def extrair_texto(mensagem):
    """Le o texto da resposta final do agente.

    O modelo responde em blocos tipados (raciocinio, texto). Aqui interessa
    apenas o texto -- os blocos de raciocinio vem sem conteudo por padrao.
    """
    return "\n".join(
        bloco["text"]
        for bloco in mensagem.content_blocks
        if bloco.get("type") == "text"
    )


def main():
    parser = argparse.ArgumentParser(
        description="SmartDocker - Analise inteligente de Dockerfiles"
    )
    parser.add_argument("caminho", help="Caminho do diretorio raiz do projeto")
    # Diretório raiz do projeto (pai de src/)
    projeto_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_output = os.path.join(projeto_dir, "relatorio.md")

    parser.add_argument(
        "-o", "--output",
        default=default_output,
        help="Caminho do arquivo de relatorio (padrao: relatorio.md na raiz)",
    )
    args = parser.parse_args()

    caminho = os.path.abspath(args.caminho)

    show_banner()

    if not os.path.isdir(caminho):
        console.print(f"[bold red]Erro: '{caminho}' nao e um diretorio valido.[/bold red]")
        sys.exit(1)

    console.print(f"[bold cyan]Projeto:[/bold cyan] {caminho}\n")

    # As tres pecas do agente.
    llm = ChatAnthropic(model="claude-sonnet-5")          # 1. o modelo
    tools = get_tools(caminho)                            # 2. as ferramentas
    agent = create_agent(                                 # 3. o loop
        llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )

    console.print("[bold]O agente esta investigando o projeto:[/bold]")

    definir_raiz(caminho)

    passo = 0
    relatorio = ""
    # O modelo chama varias ferramentas em paralelo e os retornos chegam fora
    # de ordem. Guardar o numero de cada chamada permite parear na tela.
    numero_da_chamada = {}

    for evento in agent.stream(
        {"messages": [("human", f"Analise o projeto no diretorio: {caminho}")]},
        stream_mode="updates",
    ):
        for no, update in evento.items():
            for mensagem in update.get("messages", []):
                # O modelo decidiu chamar ferramentas.
                if isinstance(mensagem, AIMessage) and mensagem.tool_calls:
                    for chamada in mensagem.tool_calls:
                        passo += 1
                        numero_da_chamada[chamada["id"]] = passo
                        log_chamada(passo, chamada["name"], chamada["args"])

                # As ferramentas responderam.
                elif isinstance(mensagem, ToolMessage):
                    log_retorno(
                        numero_da_chamada.get(mensagem.tool_call_id, passo),
                        str(mensagem.content),
                    )

                # Mensagem do modelo sem chamada de ferramenta: e o relatorio.
                elif isinstance(mensagem, AIMessage):
                    relatorio = extrair_texto(mensagem)

    console.print()
    console.rule(style="cyan")
    console.print()
    console.print(Markdown(relatorio))
    console.print()
    console.rule(style="cyan")
    console.print()

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(relatorio)

    console.print(Panel(
        f"[bold green]Relatorio salvo em:[/bold green] {args.output}",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
