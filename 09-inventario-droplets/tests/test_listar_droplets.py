"""Testes de integração: a ferramenta contra a conta DigitalOcean real, sem mock.

Cada caso roda nas duas formas. A conta pode ter outros Droplets, então o resultado é
comparado só com os da tag da suíte.
"""

import json

import pytest

from conftest import TAG
from src.ferramentas.docstring import listar_droplets as forma_docstring
from src.ferramentas.modelo_pydantic import listar_droplets as forma_pydantic

pytestmark = pytest.mark.usefixtures("cenario")

FORMAS = pytest.mark.parametrize(
    "ferramenta", [forma_docstring, forma_pydantic], ids=["docstring", "pydantic"]
)


def nomes(resultado: str) -> set[str]:
    """Nomes dos Droplets devolvidos, só os da tag da suíte."""
    return {d["nome"] for d in json.loads(resultado) if TAG in d["tags"]}


@FORMAS
@pytest.mark.parametrize(
    "argumentos, esperado",
    [
        ({}, {"teste-web-01", "teste-batch-01"}),
        ({"regiao": "nyc1"}, {"teste-web-01"}),
        ({"status": "active"}, {"teste-web-01"}),
        ({"status": "off"}, {"teste-batch-01"}),
        ({"memoria_minima_mb": 1024}, {"teste-web-01"}),
        ({"memoria_maxima_mb": 512}, {"teste-batch-01"}),
        ({"memoria_minima_mb": 1024, "memoria_maxima_mb": 1024}, {"teste-web-01"}),
        ({"status": "active", "memoria_minima_mb": 1024}, {"teste-web-01"}),
        ({"regiao": "ams3", "status": "active"}, set()),
    ],
)
def test_filtros(ferramenta, argumentos, esperado):
    assert nomes(ferramenta.invoke(argumentos)) == esperado


@FORMAS
def test_formato_do_retorno(ferramenta):
    resultado = ferramenta.invoke({"regiao": "nyc1"})

    droplet = next(d for d in json.loads(resultado) if d["nome"] == "teste-web-01")
    assert set(droplet) == {
        "id", "nome", "status", "regiao", "tamanho", "vcpus",
        "memoria_mb", "disco_gb", "ip_publico", "tags", "criado_em",
    }
    assert droplet["regiao"] == "nyc1"
    assert droplet["status"] == "active"
    assert droplet["tamanho"] == "s-1vcpu-1gb"
    assert droplet["memoria_mb"] == 1024
    assert TAG in droplet["tags"]


# Só a forma docstring: sem validação, o argumento fora da regra chega à função,
# que lista a conta e devolve vazio, sem erro.
@pytest.mark.parametrize(
    "argumentos",
    [
        {"regiao": "NYC-1"},
        {"memoria_minima_mb": 2048, "memoria_maxima_mb": 1024},
    ],
)
def test_docstring_aceita_argumento_fora_da_regra(argumentos):
    assert nomes(forma_docstring.invoke(argumentos)) == set()
