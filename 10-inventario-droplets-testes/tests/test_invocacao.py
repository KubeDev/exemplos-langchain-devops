import json
import os

import pytest
from langchain.messages import ToolMessage

from src.ferramentas.modelo_pydantic import listar_droplets

# Estes testes chamam a API da DigitalOcean de verdade, com o token só de leitura.
pytestmark = pytest.mark.skipif(
    not os.environ.get("DIGITALOCEAN_TOKEN"), reason="sem DIGITALOCEAN_TOKEN"
)

TAG_DO_LABORATORIO = "inventario-droplets"

CHAVES_DO_RESUMO = {
    "id", "nome", "status", "regiao", "tamanho", "vcpus",
    "memoria_mb", "disco_gb", "ip_publico", "tags", "criado_em",
}

# O laboratório do setup/: web-01 (nyc1, 2048 MB, active), worker-01 (nyc1, 1024 MB, active)
# e batch-01 (sfo3, 1024 MB, off). Cada filtro tem uma resposta esperada.
CRITERIOS = [
    ({"regiao": "nyc1"}, {"web-01", "worker-01"}),
    ({"status": "active"}, {"web-01", "worker-01"}),
    ({"status": "off"}, {"batch-01"}),
    ({"memoria_minima_mb": 2048}, {"web-01"}),
    ({"memoria_maxima_mb": 1024}, {"worker-01", "batch-01"}),
]


def exigir_laboratorio():
    # Sem o laboratório, o teste falha dizendo o que fazer, em vez de passar com lista vazia.
    todos = json.loads(listar_droplets.invoke({}))
    if not any(TAG_DO_LABORATORIO in droplet["tags"] for droplet in todos):
        pytest.fail(
            "Nenhum Droplet com a tag inventario-droplets. "
            "Rode o setup deste exemplo: uv run setup/criar_droplets.py"
        )


def do_laboratorio(resultado: str) -> set[str]:
    # A conta pode ter outros Droplets: o critério vale só para os do laboratório.
    return {
        droplet["nome"]
        for droplet in json.loads(resultado)
        if TAG_DO_LABORATORIO in droplet["tags"]
    }


@pytest.mark.parametrize(
    "argumentos, esperados",
    CRITERIOS,
    ids=["regiao", "status-active", "status-off", "memoria-minima", "memoria-maxima"],
)
def test_invoke_com_argumentos(argumentos, esperados):
    # O teste no lugar da aplicação: executa a ferramenta com os argumentos.
    exigir_laboratorio()

    resultado = listar_droplets.invoke(argumentos)

    assert do_laboratorio(resultado) == esperados


def test_invoke_devolve_o_resumo():
    exigir_laboratorio()

    droplets = json.loads(listar_droplets.invoke({}))

    assert all(set(droplet) == CHAVES_DO_RESUMO for droplet in droplets)


def test_invoke_com_pedido_de_chamada():
    # O teste no lugar do modelo: escreve à mão o pedido que ele faria.
    exigir_laboratorio()
    pedido = {
        "type": "tool_call",
        "name": "listar_droplets",
        "args": {"regiao": "nyc1"},
        "id": "pedido-1",
    }

    mensagem = listar_droplets.invoke(pedido)

    assert isinstance(mensagem, ToolMessage)
    assert mensagem.tool_call_id == "pedido-1"
    assert mensagem.status == "success"
    assert do_laboratorio(mensagem.content) == {"web-01", "worker-01"}
