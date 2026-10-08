import json
import os

import pytest
from pydantic import ValidationError

from src.ferramentas import docstring, modelo_pydantic

com_token = pytest.mark.skipif(
    not os.environ.get("DIGITALOCEAN_TOKEN"), reason="sem DIGITALOCEAN_TOKEN"
)

# Dois argumentos fora da regra: um formato (pattern) e uma regra entre campos (model_validator).
FORA_DA_REGRA = pytest.mark.parametrize(
    "argumentos",
    [{"regiao": "NYC-1"}, {"memoria_minima_mb": 2048, "memoria_maxima_mb": 1024}],
    ids=["regiao", "minima-acima-da-maxima"],
)


@FORA_DA_REGRA
def test_pydantic_recusa_argumento_fora_da_regra(argumentos):
    # A validação barra antes de a função rodar: nada sai da máquina.
    with pytest.raises(ValidationError):
        modelo_pydantic.listar_droplets.invoke(argumentos)


@com_token
@FORA_DA_REGRA
def test_docstring_deixa_argumento_fora_da_regra_chegar_na_execucao(argumentos):
    # Sem a regra no esquema, o valor passa, a função roda e responde sem erro.
    resultado = docstring.listar_droplets.invoke(argumentos)

    # Uma lista vazia que parece resposta válida.
    assert json.loads(resultado) == []


@pytest.mark.parametrize(
    "ferramenta",
    [docstring.listar_droplets, modelo_pydantic.listar_droplets],
    ids=["docstring", "pydantic"],
)
def test_tipo_errado_recusado_nas_duas_formas(ferramenta):
    # O tipo está no esquema das duas formas; só as regras ficaram de fora de uma.
    with pytest.raises(ValidationError):
        ferramenta.invoke({"memoria_minima_mb": "muita"})


def test_pedido_de_chamada_invalido_nao_vira_mensagem():
    # A ferramenta lança a exceção; quem a transforma em mensagem para o modelo é o agente.
    pedido = {
        "type": "tool_call",
        "name": "listar_droplets",
        "args": {"regiao": "NYC-1"},
        "id": "pedido-2",
    }

    with pytest.raises(ValidationError):
        modelo_pydantic.listar_droplets.invoke(pedido)
