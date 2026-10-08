import asyncio
import json
import os

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from src import servidor


def chamar(ferramenta: str, argumentos: dict):
    # O teste no lugar do cliente MCP: fala com o server em memória, sem subprocesso.
    async def executar():
        async with Client(servidor.mcp) as cliente:
            return await cliente.call_tool(ferramenta, argumentos)

    return asyncio.run(executar())


def texto(resultado) -> str:
    # O conteúdo de texto é o que o modelo lê.
    return resultado.content[0].text


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
        "desligar_droplet",
    }


def test_versao_no_server_info():
    async def versao():
        async with Client(servidor.mcp) as cliente:
            return cliente.server_info.version

    assert asyncio.run(versao()) == "1.1.0"


def test_chamado_encontrado_com_id_em_minusculas():
    chamado = json.loads(texto(chamar("consultar_chamado", {"chamado_id": "ch-1042"})))

    assert chamado["servico"] == "checkout-api"


# Escopo declarado no retorno, a lição do 14: a MUD-305 fica fora do período padrão.


def test_com_escopo_o_vazio_declara_o_recorte():
    lido = texto(chamar("consultar_historico_mudancas", {"servico": "fila-pedidos"}))

    assert "filtro: servico=fila-pedidos" in lido
    assert "últimas 24 horas" in lido
    assert "valor_padrao_aplicado: horas=24" in lido
    assert "consultado_em: 2026-10-06T16:30:00-03:00" in lido
    assert "informe horas para ampliar" in lido


def test_ampliar_o_periodo_encontra_a_mudanca():
    resultado = chamar("consultar_historico_mudancas", {"servico": "fila-pedidos", "horas": 168})

    assert [mudanca["id"] for mudanca in resultado.structured_content["itens"]] == ["MUD-305"]
    assert "valor_padrao_aplicado: nenhum" in texto(resultado)


def test_periodo_padrao_alcanca_a_mudanca_da_tarde():
    resultado = chamar("consultar_historico_mudancas", {"servico": "checkout-api"})

    assert [mudanca["id"] for mudanca in resultado.structured_content["itens"]] == ["MUD-311"]


def test_escopo_no_texto_que_o_modelo_le():
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


def test_runbook_vazio_declara_filtro_e_catalogo():
    lido = texto(chamar("buscar_runbook", {"servico": "Checkout-API"}))

    assert "filtro: servico=Checkout-API" in lido
    assert "0 de 3 runbooks do catálogo" in lido


def test_runbook_por_id():
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
def test_listar_droplets_declara_pagina_e_total():
    resultado = chamar("listar_droplets", {"regiao": "nyc1", "limite": 1})
    escopo = resultado.structured_content["escopo"]
    itens = resultado.structured_content["itens"]

    assert "filtro: regiao=nyc1" in texto(resultado)
    assert "pagina: 1 (1 por página)" in texto(resultado)
    assert escopo["retornados"].startswith(f"{len(itens)} de ")
    assert all(droplet["regiao"] == "nyc1" for droplet in itens)


# Escrita controlada: desligar_droplet com um cliente falso, sem token e sem API.


class ClienteFalso:
    # Só o que desligar_droplet usa do pydo: listar por tag e disparar a action.
    def __init__(self, droplets: list[dict]):
        self.acoes = []
        self.droplets = self
        self.droplet_actions = self
        self._droplets = droplets

    def list(self, tag_name):
        return {"droplets": [item for item in self._droplets if tag_name in item["tags"]]}

    def post(self, droplet_id, body):
        self.acoes.append((droplet_id, body))
        return {"action": {"id": 900, "status": "in-progress", "started_at": "2026-10-06T19:30:00Z"}}


@pytest.fixture
def cliente_falso(monkeypatch):
    monkeypatch.setenv("DIGITALOCEAN_TOKEN_ESCRITA", "token-falso")
    falso = ClienteFalso(
        [
            {"id": 501, "name": "web-01", "status": "active", "tags": ["inventario-droplets", "web"]},
            {"id": 503, "name": "batch-01", "status": "off", "tags": ["inventario-droplets", "batch"]},
            {"id": 777, "name": "worker-01", "status": "active", "tags": ["producao"]},
        ]
    )
    monkeypatch.setattr(servidor, "Client", lambda token: falso)
    return falso


def test_anotacoes_de_leitura_e_escrita():
    # Dica ao cliente, não controle: o server declara, o cliente decide o que fazer com isso.
    async def listar():
        async with Client(servidor.mcp) as cliente:
            return await cliente.list_tools()

    anotacoes = {ferramenta.name: ferramenta.annotations for ferramenta in asyncio.run(listar())}

    assert anotacoes["desligar_droplet"].read_only_hint is False
    assert anotacoes["desligar_droplet"].destructive_hint is True
    assert anotacoes["listar_droplets"].read_only_hint is True


def test_esquema_so_aceita_droplets_do_laboratorio():
    async def esquema():
        async with Client(servidor.mcp) as cliente:
            ferramentas = await cliente.list_tools()
        return next(f for f in ferramentas if f.name == "desligar_droplet").input_schema

    assert asyncio.run(esquema())["properties"]["droplet"]["enum"] == ["web-01", "worker-01", "batch-01"]


def test_droplet_fora_do_recorte_barrado_no_esquema(cliente_falso):
    # A validação acontece antes da função: nenhuma chamada chega ao cliente.
    with pytest.raises(ToolError, match="validation error"):
        chamar("desligar_droplet", {"droplet": "db-producao"})

    assert cliente_falso.acoes == []


def test_nome_permitido_sem_a_tag_recusado_antes_da_acao(cliente_falso):
    # worker-01 existe, mas sem a tag do laboratório: o nome sozinho não autoriza.
    with pytest.raises(ToolError, match="não tem a tag inventario-droplets"):
        chamar("desligar_droplet", {"droplet": "worker-01"})

    assert cliente_falso.acoes == []


def test_shutdown_declara_o_efeito(cliente_falso):
    resultado = chamar("desligar_droplet", {"droplet": "web-01"})
    lido = texto(resultado)

    assert cliente_falso.acoes == [(501, {"type": "shutdown"})]
    assert "pedido: shutdown gracioso de web-01 (501)" in lido
    assert "estado_anterior: active" in lido
    assert "acao_disparada: shutdown, action 900, status in-progress" in lido
    assert "nenhum power_off, reboot ou destroy" in lido
    assert "power_on" in lido


def test_nome_duplicado_no_laboratorio_recusado(cliente_falso):
    # Nome não é único no DigitalOcean: com dois web-01 na tag, o server não escolhe um.
    cliente_falso._droplets.append(
        {"id": 502, "name": "web-01", "status": "active", "tags": ["inventario-droplets", "web"]}
    )

    with pytest.raises(ToolError, match="Há 2 Droplets web-01"):
        chamar("desligar_droplet", {"droplet": "web-01"})

    assert cliente_falso.acoes == []


def test_droplet_ja_desligado_nao_dispara_acao(cliente_falso):
    lido = texto(chamar("desligar_droplet", {"droplet": "batch-01"}))

    assert cliente_falso.acoes == []
    assert "acao_disparada: nenhuma: o Droplet já estava desligado" in lido


def test_power_off_e_destroy_nao_publicados():
    async def listar():
        async with Client(servidor.mcp) as cliente:
            return await cliente.list_tools()

    nomes = " ".join(ferramenta.name for ferramenta in asyncio.run(listar()))

    assert "power_off" not in nomes
    assert "destr" not in nomes
    assert "reboot" not in nomes


# Escrita real: só com o token de escrita E o nome de um Droplet ATIVO na linha de comando
# (web-01 ou worker-01; o batch-01 do laboratório já fica desligado). Religue-o depois.
# Ter o token no .env não basta: desligar um Droplet nunca acontece por acaso num `uv run pytest`.


@pytest.mark.skipif(
    not (os.getenv("DIGITALOCEAN_TOKEN_ESCRITA") and os.getenv("DROPLET_TESTE")),
    reason="sem DIGITALOCEAN_TOKEN_ESCRITA e DROPLET_TESTE",
)
def test_desliga_o_droplet_de_teste():
    lido = texto(chamar("desligar_droplet", {"droplet": os.environ["DROPLET_TESTE"]}))

    assert f"shutdown gracioso de {os.environ['DROPLET_TESTE']}" in lido
    assert "estado_anterior: active" in lido
    assert "acao_disparada: shutdown, action" in lido
