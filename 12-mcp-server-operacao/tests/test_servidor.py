import asyncio
import json
import os

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from src.servidor import mcp


def chamar(ferramenta: str, argumentos: dict):
    # O teste no lugar do cliente MCP: fala com o server em memória, sem subprocesso.
    async def executar():
        async with Client(mcp) as cliente:
            return await cliente.call_tool(ferramenta, argumentos)

    return asyncio.run(executar()).data


def test_catalogo_publicado():
    async def listar():
        async with Client(mcp) as cliente:
            return await cliente.list_tools()

    nomes = {ferramenta.name for ferramenta in asyncio.run(listar())}

    assert nomes == {
        "listar_droplets",
        "consultar_chamado",
        "buscar_runbook",
        "consultar_historico_mudancas",
    }


def test_chamado_encontrado_com_id_em_minusculas():
    chamado = json.loads(chamar("consultar_chamado", {"chamado_id": "ch-1042"}))

    assert chamado["servico"] == "checkout-api"


def test_chamado_inexistente():
    resultado = chamar("consultar_chamado", {"chamado_id": "CH-9999"})

    assert resultado == "Chamado CH-9999 não encontrado."


def test_runbook_por_servico():
    runbooks = json.loads(chamar("buscar_runbook", {"servico": "checkout-api"}))

    assert {runbook["id"] for runbook in runbooks} == {"RB-101", "RB-102"}


def test_runbook_por_id():
    runbooks = json.loads(chamar("buscar_runbook", {"runbook_id": "rb-205"}))

    assert [runbook["servico"] for runbook in runbooks] == ["fila-pedidos"]


def test_historico_da_mudanca_mais_recente_para_a_mais_antiga():
    mudancas = json.loads(chamar("consultar_historico_mudancas", {"servico": "checkout-api"}))

    assert [mudanca["id"] for mudanca in mudancas] == ["MUD-311", "MUD-298"]


def test_regiao_fora_do_esquema_barrada_no_server():
    # A validação acontece antes da função: não precisa de token.
    with pytest.raises(ToolError, match="validation error"):
        chamar("listar_droplets", {"regiao": "NYC-1"})


@pytest.mark.skipif(not os.getenv("DIGITALOCEAN_TOKEN"), reason="sem DIGITALOCEAN_TOKEN")
def test_listar_droplets_por_regiao():
    droplets = json.loads(chamar("listar_droplets", {"regiao": "nyc1"}))

    nomes = {droplet["nome"] for droplet in droplets}

    # Laboratório: web-01 e worker-01 em nyc1, batch-01 em sfo3.
    assert {"web-01", "worker-01"} <= nomes
    assert "batch-01" not in nomes
