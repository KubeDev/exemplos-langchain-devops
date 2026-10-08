import asyncio
import json
import os

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from src import servidor
from src.retornos import com_escopo, sem_escopo


def chamar(ferramenta: str, argumentos: dict):
    # O teste no lugar do cliente MCP: fala com o server em memória, sem subprocesso.
    async def executar():
        async with Client(servidor.mcp) as cliente:
            return await cliente.call_tool(ferramenta, argumentos)

    return asyncio.run(executar())


def texto(resultado) -> str:
    # O conteúdo de texto é o que o modelo lê.
    return resultado.content[0].text


@pytest.fixture
def retorno_com_escopo(monkeypatch):
    # A mesma troca de módulo do servidor.py, feita só durante o teste.
    monkeypatch.setattr(servidor, "retornar", com_escopo.retornar)


@pytest.fixture
def retorno_sem_escopo(monkeypatch):
    monkeypatch.setattr(servidor, "retornar", sem_escopo.retornar)


def test_catalogo_publicado():
    async def listar():
        async with Client(servidor.mcp) as cliente:
            return await cliente.list_tools()

    nomes = {ferramenta.name for ferramenta in asyncio.run(listar())}

    assert nomes == {
        "listar_droplets",
        "consultar_chamado",
        "buscar_runbook",
        "consultar_historico_mudancas",
    }


def test_versao_no_server_info():
    async def versao():
        async with Client(servidor.mcp) as cliente:
            return cliente.server_info.version

    assert asyncio.run(versao()) == "1.0.0"


def test_chamado_encontrado_com_id_em_minusculas():
    chamado = json.loads(texto(chamar("consultar_chamado", {"chamado_id": "ch-1042"})))

    assert chamado["servico"] == "checkout-api"


# Falha silenciosa: a mudança MUD-305 existe, mas fica fora do período padrão.


def test_sem_escopo_o_vazio_parece_resposta(retorno_sem_escopo):
    resultado = chamar("consultar_historico_mudancas", {"servico": "fila-pedidos"})

    assert texto(resultado) == "[]"
    assert resultado.is_error is False


def test_com_escopo_o_vazio_declara_o_recorte(retorno_com_escopo):
    lido = texto(chamar("consultar_historico_mudancas", {"servico": "fila-pedidos"}))

    assert "filtro: servico=fila-pedidos" in lido
    assert "últimas 24 horas" in lido
    assert "valor_padrao_aplicado: horas=24" in lido
    assert "consultado_em: 2026-10-06T16:30:00-03:00" in lido
    assert "informe horas para ampliar" in lido


def test_ampliar_o_periodo_encontra_a_mudanca(retorno_com_escopo):
    resultado = chamar("consultar_historico_mudancas", {"servico": "fila-pedidos", "horas": 168})

    assert [mudanca["id"] for mudanca in resultado.structured_content["itens"]] == ["MUD-305"]
    assert "valor_padrao_aplicado: nenhum" in texto(resultado)


def test_periodo_padrao_alcanca_a_mudanca_da_tarde(retorno_com_escopo):
    resultado = chamar("consultar_historico_mudancas", {"servico": "checkout-api"})

    assert [mudanca["id"] for mudanca in resultado.structured_content["itens"]] == ["MUD-311"]


def test_escopo_no_texto_que_o_modelo_le(retorno_com_escopo):
    # O cliente LangChain entrega ao modelo só o texto; o conteúdo estruturado vira artefato.
    resultado = chamar("consultar_historico_mudancas", {"servico": "fila-pedidos"})

    for chave, valor in resultado.structured_content["escopo"].items():
        assert f"{chave}: {valor}" in texto(resultado)


def test_periodo_padrao_fora_do_esquema():
    # Trocar PERIODO_PADRAO_HORAS não muda o esquema: nenhum teste de esquema acusa a quebra.
    async def esquema():
        async with Client(servidor.mcp) as cliente:
            ferramentas = await cliente.list_tools()
        return next(f for f in ferramentas if f.name == "consultar_historico_mudancas").input_schema

    horas = asyncio.run(esquema())["properties"]["horas"]

    assert horas.get("default") is None


def test_runbook_vazio_declara_filtro_e_catalogo(retorno_com_escopo):
    lido = texto(chamar("buscar_runbook", {"servico": "Checkout-API"}))

    assert "filtro: servico=Checkout-API" in lido
    assert "0 de 3 runbooks do catálogo" in lido


def test_runbook_por_id(retorno_com_escopo):
    resultado = chamar("buscar_runbook", {"runbook_id": "rb-205"})

    assert [runbook["servico"] for runbook in resultado.structured_content["itens"]] == ["fila-pedidos"]


DROPLET_DA_API = {
    "id": 501,
    "name": "web-01",
    "status": "active",
    "region": {"slug": "nyc1"},
    "size_slug": "s-1vcpu-1gb",
    "vcpus": 1,
    "memory": 1024,
    "disk": 25,
    "tags": ["inventario-droplets"],
    "created_at": "2026-10-01T12:00:00Z",
    "networks": {
        "v4": [
            {"type": "private", "ip_address": "10.0.0.2"},
            {"type": "public", "ip_address": "203.0.113.10"},
        ]
    },
}


def test_droplet_resumido_com_nome_e_id():
    assert servidor.resumir_droplet(DROPLET_DA_API) == {
        "droplet": "web-01 (501)",
        "status": "active",
        "regiao": "nyc1",
    }


def test_droplet_completo_com_campos_principais():
    assert servidor.detalhar_droplet(DROPLET_DA_API) == {
        "id": 501,
        "nome": "web-01",
        "status": "active",
        "regiao": "nyc1",
        "tamanho": "s-1vcpu-1gb",
        "vcpus": 1,
        "memoria_mb": 1024,
        "disco_gb": 25,
        "ip_publico": "203.0.113.10",
        "tags": ["inventario-droplets"],
        "criado_em": "2026-10-01T12:00:00Z",
    }


def test_regiao_fora_do_esquema_barrada_no_server():
    # A validação acontece antes da função: não precisa de token.
    with pytest.raises(ToolError, match="validation error"):
        chamar("listar_droplets", {"regiao": "NYC-1"})


@pytest.mark.skipif(not os.getenv("DIGITALOCEAN_TOKEN"), reason="sem DIGITALOCEAN_TOKEN")
def test_listar_droplets_declara_pagina_e_total(retorno_com_escopo):
    resultado = chamar("listar_droplets", {"regiao": "nyc1", "limite": 1})
    escopo = resultado.structured_content["escopo"]
    itens = resultado.structured_content["itens"]

    total = int(escopo["retornados"].split(" de ")[1])

    # Sem contagem fixa: o total é o da região, seja qual for o laboratório na conta.
    assert "filtro: regiao=nyc1" in texto(resultado)
    assert "pagina: 1 (1 por página)" in texto(resultado)
    assert escopo["retornados"] == f"{len(itens)} de {total}"
    assert escopo["proxima_pagina"] == (2 if total > 1 else "nenhuma")
    assert all(droplet["regiao"] == "nyc1" for droplet in itens)


@pytest.mark.skipif(not os.getenv("DIGITALOCEAN_TOKEN"), reason="sem DIGITALOCEAN_TOKEN")
def test_listar_droplets_sem_regiao_declara_todas(retorno_com_escopo):
    resultado = chamar("listar_droplets", {})
    escopo = resultado.structured_content["escopo"]

    assert "filtro: todas as regiões" in texto(resultado)
    assert escopo["retornados"].startswith(f"{len(resultado.structured_content['itens'])} de ")
