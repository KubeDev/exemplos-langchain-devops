import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Literal

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.tools import ToolResult
from pydantic import Field
from pydo import Client

# Troque o módulo para mudar o retorno das ferramentas:
# sem_escopo · com_escopo
from src.retornos.sem_escopo import retornar

load_dotenv()

DADOS = Path(__file__).resolve().parent.parent / "dados"

# Relógio dos dados fictícios: as consultas a dados/ partem deste instante,
# para a demonstração dar o mesmo resultado em qualquer dia.
AGORA_DADOS = datetime.fromisoformat("2026-10-06T16:30:00-03:00")

# Valor padrão aplicado pelo server quando o consumidor não informa o período.
# Ele não aparece no esquema: trocá-lo não muda o esquema, mas muda o que todo consumidor recebe.
PERIODO_PADRAO_HORAS = 24

# Descrição, esquema e retorno formam o contrato público do server; a versão vai no serverInfo.
# Compatível (sobe o minor): parâmetro opcional novo, campo novo no retorno.
# Quebra (sobe o major): renomear ou remover ferramenta, parâmetro ou campo; tornar um parâmetro
# obrigatório; trocar um valor padrão, como PERIODO_PADRAO_HORAS; reescrever uma descrição.
mcp = FastMCP("operacao", version="1.0.0")


def ler(arquivo: str) -> list[dict]:
    return json.loads((DADOS / arquivo).read_text(encoding="utf-8"))


def registrar(chamada: str) -> None:
    # No transporte stdio, o stdout é o canal do protocolo: o log vai para o stderr.
    print(f"Ferramenta: {chamada}", file=sys.stderr)


def resumir_droplet(droplet: dict) -> dict:
    # Nome junto do ID: o consumidor cita um Droplet que a pessoa reconhece.
    return {
        "droplet": f"{droplet['name']} ({droplet['id']})",
        "status": droplet["status"],
        "regiao": droplet["region"]["slug"],
    }


def detalhar_droplet(droplet: dict) -> dict:
    # Os campos principais, os mesmos do 09 e do 13: nunca o objeto inteiro da API.
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


@mcp.tool
def listar_droplets(
    regiao: Annotated[
        str | None,
        Field(pattern=r"^[a-z]{3}[0-9]$", description="Região do Droplet. Sem região, lista todos."),
    ] = None,
    detalhe: Annotated[
        Literal["resumido", "completo"],
        Field(description="resumido traz nome com ID, status e região; completo acrescenta tamanho, vCPUs, memória, disco, IP público, tags e criação."),
    ] = "resumido",
    pagina: Annotated[int, Field(ge=1, description="Página do resultado, a partir de 1.")] = 1,
    limite: Annotated[int, Field(ge=1, le=50, description="Droplets por página, até 50.")] = 20,
) -> ToolResult:
    """Lista os Droplets da conta DigitalOcean, com filtro opcional por região, uma página por chamada."""
    registrar(f"listar_droplets(regiao={regiao!r}, detalhe={detalhe!r}, pagina={pagina}, limite={limite})")

    cliente = Client(token=os.environ["DIGITALOCEAN_TOKEN"])
    droplets = cliente.droplets.list(per_page=200)["droplets"]

    # O filtro é feito aqui, então a página também: primeiro filtra, depois corta.
    if regiao:
        droplets = [droplet for droplet in droplets if droplet["region"]["slug"] == regiao]

    total = len(droplets)
    droplets = droplets[(pagina - 1) * limite : pagina * limite]
    formatar = resumir_droplet if detalhe == "resumido" else detalhar_droplet
    droplets = [formatar(droplet) for droplet in droplets]

    escopo = {
        "filtro": f"regiao={regiao}" if regiao else "todas as regiões",
        "detalhe": detalhe,
        "pagina": f"{pagina} ({limite} por página)",
        "retornados": f"{len(droplets)} de {total}",
        "proxima_pagina": pagina + 1 if pagina * limite < total else "nenhuma",
        "consultado_em": datetime.now(UTC).isoformat(timespec="seconds"),
    }

    return retornar(droplets, escopo)


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
def buscar_runbook(servico: str | None = None, runbook_id: str | None = None) -> ToolResult:
    """Busca runbooks de operação pelo serviço, como checkout-api, ou pelo identificador, como RB-101.

    Retorna os passos de cada runbook encontrado.
    """
    registrar(f"buscar_runbook(servico={servico!r}, runbook_id={runbook_id!r})")

    catalogo = ler("runbooks.json")
    runbooks = [
        runbook
        for runbook in catalogo
        if runbook["servico"] == servico or runbook["id"] == (runbook_id or "").upper()
    ]

    filtros = {"servico": servico, "runbook_id": runbook_id}
    escopo = {
        "filtro": ", ".join(f"{campo}={valor}" for campo, valor in filtros.items() if valor) or "nenhum",
        "comparacao": "nome exato do serviço; identificador sem diferenciar maiúsculas",
        "retornados": f"{len(runbooks)} de {len(catalogo)} runbooks do catálogo",
        "consultado_em": AGORA_DADOS.isoformat(),
    }

    return retornar(runbooks, escopo)


@mcp.tool
def consultar_historico_mudancas(
    servico: str,
    horas: Annotated[
        int | None,
        Field(ge=1, description="Janela em horas até o momento da consulta. Sem valor, o server aplica o período padrão."),
    ] = None,
) -> ToolResult:
    """Consulta o histórico de mudanças de um serviço, como checkout-api, da mais recente para a mais antiga.

    Retorna versão anterior, horário e responsável de cada mudança.
    """
    registrar(f"consultar_historico_mudancas(servico={servico!r}, horas={horas!r})")

    padrao_aplicado = horas is None
    horas = horas or PERIODO_PADRAO_HORAS
    desde = AGORA_DADOS - timedelta(hours=horas)

    mudancas = [
        mudanca
        for mudanca in ler("mudancas.json")
        if mudanca["servico"] == servico and datetime.fromisoformat(mudanca["executada_em"]) >= desde
    ]
    mudancas.sort(key=lambda mudanca: mudanca["executada_em"], reverse=True)

    escopo = {
        "filtro": f"servico={servico}",
        "periodo": f"últimas {horas} horas, de {desde.isoformat()} até {AGORA_DADOS.isoformat()}",
        "valor_padrao_aplicado": f"horas={PERIODO_PADRAO_HORAS}" if padrao_aplicado else "nenhum",
        "retornados": f"{len(mudancas)} (todas as mudanças do período)",
        "fora_do_escopo": "mudanças anteriores ao período não foram consultadas; informe horas para ampliar",
        "consultado_em": AGORA_DADOS.isoformat(),
    }

    return retornar(mudancas, escopo)


def main() -> None:
    mcp.run(show_banner=False)


if __name__ == "__main__":
    main()
