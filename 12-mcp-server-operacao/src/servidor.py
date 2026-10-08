import json
import os
import sys
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import Field
from pydo import Client

load_dotenv()

DADOS = Path(__file__).resolve().parent.parent / "dados"

mcp = FastMCP("operacao")


def ler(arquivo: str) -> list[dict]:
    return json.loads((DADOS / arquivo).read_text(encoding="utf-8"))


def resumir(droplet) -> dict:
    ip_publico = next(
        (rede["ip_address"] for rede in droplet["networks"]["v4"] if rede["type"] == "public"),
        None,
    )
    return {
        "id": droplet["id"],
        "nome": droplet["name"],
        "status": droplet["status"],
        "regiao": droplet["region"]["slug"],
        "tamanho": droplet["size_slug"],
        "vcpus": droplet["vcpus"],
        "memoria_mb": droplet["memory"],
        "disco_gb": droplet["disk"],
        "ip_publico": ip_publico,
        "tags": droplet["tags"],
        "criado_em": droplet["created_at"],
    }


def registrar(chamada: str) -> None:
    # No transporte stdio, o stdout é o canal do protocolo: o log vai para o stderr.
    print(f"Ferramenta: {chamada}", file=sys.stderr)


@mcp.tool
def listar_droplets(
    regiao: Annotated[
        str | None,
        Field(pattern=r"^[a-z]{3}[0-9]$", description="Região do Droplet. Sem região, lista todos."),
    ] = None,
) -> str:
    """Lista os Droplets da conta DigitalOcean, com filtro opcional por região."""
    registrar(f"listar_droplets(regiao={regiao!r})")

    cliente = Client(token=os.environ["DIGITALOCEAN_TOKEN"])
    droplets = cliente.droplets.list()["droplets"]

    if regiao:
        droplets = [droplet for droplet in droplets if droplet["region"]["slug"] == regiao]

    return json.dumps([resumir(droplet) for droplet in droplets], ensure_ascii=False)


@mcp.tool
def consultar_chamado(chamado_id: str) -> str:
    """Consulta um chamado de operação pelo identificador, como CH-1042.

    Retorna serviço afetado, severidade, status e descrição do chamado.
    """
    registrar(f"consultar_chamado(chamado_id={chamado_id!r})")

    for chamado in ler("chamados.json"):
        if chamado["id"] == chamado_id.upper():
            return json.dumps(chamado, ensure_ascii=False)

    return f"Chamado {chamado_id} não encontrado."


@mcp.tool
def buscar_runbook(servico: str | None = None, runbook_id: str | None = None) -> str:
    """Busca runbooks de operação pelo serviço, como checkout-api, ou pelo identificador, como RB-101.

    Retorna os passos de cada runbook encontrado.
    """
    registrar(f"buscar_runbook(servico={servico!r}, runbook_id={runbook_id!r})")

    runbooks = [
        runbook
        for runbook in ler("runbooks.json")
        if runbook["servico"] == servico or runbook["id"] == (runbook_id or "").upper()
    ]

    return json.dumps(runbooks, ensure_ascii=False)


@mcp.tool
def consultar_historico_mudancas(servico: str) -> str:
    """Consulta o histórico de mudanças de um serviço, como checkout-api, da mais recente para a mais antiga.

    Retorna versão anterior, horário e responsável de cada mudança.
    """
    registrar(f"consultar_historico_mudancas(servico={servico!r})")

    mudancas = [mudanca for mudanca in ler("mudancas.json") if mudanca["servico"] == servico]
    mudancas.sort(key=lambda mudanca: mudanca["executada_em"], reverse=True)

    return json.dumps(mudancas, ensure_ascii=False)


def main() -> None:
    mcp.run(show_banner=False)


if __name__ == "__main__":
    main()
