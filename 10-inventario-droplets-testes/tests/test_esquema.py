from src.ferramentas import docstring, modelo_pydantic


def argumentos(ferramenta) -> dict:
    # O mesmo esquema que vai ao modelo: um campo por argumento.
    return ferramenta.tool_call_schema.model_json_schema()["properties"]


def test_docstring_regras_so_em_prosa():
    campos = argumentos(docstring.listar_droplets)

    assert "pattern" not in campos["regiao"]["anyOf"][0]
    assert "enum" not in campos["status"]["anyOf"][0]
    assert "minimum" not in campos["memoria_minima_mb"]["anyOf"][0]
    assert "nyc1" in docstring.listar_droplets.description
    assert "maior ou igual à mínima" in docstring.listar_droplets.description


def test_pydantic_regras_no_esquema():
    campos = argumentos(modelo_pydantic.listar_droplets)

    assert campos["regiao"]["anyOf"][0]["pattern"] == r"^[a-z]{3}[0-9]$"
    assert campos["status"]["anyOf"][0]["enum"] == ["new", "active", "off", "archive"]
    assert campos["memoria_minima_mb"]["anyOf"][0]["minimum"] == 512
    assert campos["memoria_maxima_mb"]["anyOf"][0]["minimum"] == 512


def test_pydantic_minima_ate_maxima_fora_do_esquema():
    # O model_validator só vale na validação: o modelo não fica sabendo da regra entre campos.
    maxima = argumentos(modelo_pydantic.listar_droplets)["memoria_maxima_mb"]

    assert maxima["anyOf"][0] == {"type": "integer", "minimum": 512}
