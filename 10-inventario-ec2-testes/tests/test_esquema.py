import pytest

from src.ferramentas import docstring, modelo_pydantic

FORMAS = [docstring.listar_instancias, modelo_pydantic.listar_instancias]
ESTADOS = ["pending", "running", "stopping", "stopped", "shutting-down", "terminated"]


def argumentos(ferramenta) -> dict:
    # O mesmo esquema que vai ao modelo: um campo por argumento.
    return ferramenta.tool_call_schema.model_json_schema()["properties"]


@pytest.mark.parametrize("ferramenta", FORMAS, ids=["forma2", "forma4"])
def test_estado_e_valor_fechado(ferramenta):
    estado = argumentos(ferramenta)["estado"]["anyOf"][0]

    assert estado["enum"] == ESTADOS


def test_forma2_sem_formato_de_regiao():
    regiao = argumentos(docstring.listar_instancias)["regiao"]

    assert "pattern" not in regiao["anyOf"][0]
    assert "us-east-1" in regiao["description"]


def test_forma4_com_formato_de_regiao():
    regiao = argumentos(modelo_pydantic.listar_instancias)["regiao"]

    assert regiao["anyOf"][0]["pattern"] == r"^[a-z]{2}(-[a-z]+)+-\d+$"
