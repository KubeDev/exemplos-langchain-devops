"""Testes de unidade: o esquema de cada forma e a validação da forma Pydantic.

Nenhum chama a DigitalOcean: o esquema é gerado localmente, e na forma Pydantic o argumento
inválido é recusado antes de a função rodar.
"""

import pytest
from pydantic import ValidationError

from src.ferramentas.docstring import listar_droplets as forma_docstring
from src.ferramentas.modelo_pydantic import listar_droplets as forma_pydantic

ARGUMENTOS = ["regiao", "status", "memoria_minima_mb", "memoria_maxima_mb"]


def campo(ferramenta, nome) -> dict:
    """O ramo não nulo do campo no JSON Schema que o modelo recebe."""
    propriedade = ferramenta.tool_call_schema.model_json_schema()["properties"][nome]
    return next(ramo for ramo in propriedade["anyOf"] if ramo["type"] != "null")


def test_mesmo_nome_e_argumentos_nas_duas_formas():
    for ferramenta in (forma_docstring, forma_pydantic):
        assert ferramenta.name == "listar_droplets"
        assert list(ferramenta.args) == ARGUMENTOS


def test_esquema_pydantic_traz_as_regras():
    assert campo(forma_pydantic, "regiao")["pattern"] == "^[a-z]{3}[0-9]$"
    assert campo(forma_pydantic, "status")["enum"] == ["new", "active", "off", "archive"]
    assert campo(forma_pydantic, "memoria_minima_mb")["minimum"] == 512
    assert campo(forma_pydantic, "memoria_maxima_mb")["minimum"] == 512


def test_regra_minima_ate_maxima_fica_fora_do_esquema():
    # O model_validator não vira JSON Schema: a máxima só carrega o próprio piso.
    assert campo(forma_pydantic, "memoria_maxima_mb") == {"minimum": 512, "type": "integer"}


def test_esquema_docstring_so_tem_tipos_e_regras_em_prosa():
    for nome in ARGUMENTOS:
        assert set(campo(forma_docstring, nome)) == {"type"}

    descricao = forma_docstring.description
    assert "nyc1" in descricao
    assert "new, active, off ou archive" in descricao
    assert "no mínimo 512" in descricao


@pytest.mark.parametrize(
    "argumentos",
    [
        {"regiao": "NYC-1"},
        {"status": "running"},
        {"memoria_minima_mb": 256},
        {"memoria_maxima_mb": 256},
        {"memoria_minima_mb": 2048, "memoria_maxima_mb": 1024},
    ],
)
def test_pydantic_recusa_argumento_fora_da_regra(argumentos):
    with pytest.raises(ValidationError):
        forma_pydantic.invoke(argumentos)
