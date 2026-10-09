# O que o modelo recebe de cada forma da ferramenta?
# Estes testes leem o esquema JSON das duas formas e comparam onde as regras ficaram.
# Não chamam a API: rodam offline, sem token.

from src.ferramentas import docstring, modelo_pydantic


def argumentos(ferramenta) -> dict:
    # O mesmo esquema que vai ao modelo: um campo por argumento.
    # tool_call_schema é o que o LangChain envia; "properties" é o dicionário campo -> regras.
    return ferramenta.tool_call_schema.model_json_schema()["properties"]


# Todo argumento é opcional (X | None), então cada campo vira
#   {"anyOf": [<tipo com as regras>, {"type": "null"}]}
# e o ["anyOf"][0] usado abaixo é o lado que carrega as regras.


def test_docstring_regras_so_em_prosa():
    # Na forma docstring, o esquema só tem o tipo; as regras ficam no texto da descrição.
    campos = argumentos(docstring.listar_droplets)

    # Nenhuma regra no esquema: sem formato, sem lista de valores, sem mínimo.
    assert "pattern" not in campos["regiao"]["anyOf"][0]
    assert "enum" not in campos["status"]["anyOf"][0]
    assert "minimum" not in campos["memoria_minima_mb"]["anyOf"][0]
    # As regras existem, mas como prosa: o modelo lê, ninguém verifica.
    assert "nyc1" in docstring.listar_droplets.description
    assert "maior ou igual à mínima" in docstring.listar_droplets.description


def test_pydantic_regras_no_esquema():
    # Na forma Pydantic, cada regra do FiltroDroplets vira uma chave do esquema.
    campos = argumentos(modelo_pydantic.listar_droplets)

    assert campos["regiao"]["anyOf"][0]["pattern"] == r"^[a-z]{3}[0-9]$"  # Field(pattern=...)
    assert campos["status"]["anyOf"][0]["enum"] == ["new", "active", "off", "archive"]  # Literal
    assert campos["memoria_minima_mb"]["anyOf"][0]["minimum"] == 512  # Field(ge=512)
    assert campos["memoria_maxima_mb"]["anyOf"][0]["minimum"] == 512  # Field(ge=512)


def test_pydantic_minima_ate_maxima_fora_do_esquema():
    # O model_validator só vale na validação: o modelo não fica sabendo da regra entre campos.
    maxima = argumentos(modelo_pydantic.listar_droplets)["memoria_maxima_mb"]

    # O campo inteiro é só tipo e mínimo: nenhuma menção à memoria_minima_mb.
    assert maxima["anyOf"][0] == {"type": "integer", "minimum": 512}
