import pytest
from botocore.exceptions import EndpointConnectionError
from pydantic import ValidationError

from src.ferramentas import docstring, modelo_pydantic


def test_forma4_recusa_regiao_fora_do_formato():
    # O pattern barra antes de a função rodar: nada sai da máquina.
    with pytest.raises(ValidationError):
        modelo_pydantic.listar_instancias.invoke({"regiao": "Virginia"})


def test_forma2_deixa_regiao_fora_do_formato_chegar_na_aws():
    # Sem pattern, o valor passa e só falha na rede, depois das novas tentativas.
    with pytest.raises(EndpointConnectionError):
        docstring.listar_instancias.invoke({"regiao": "Virginia"})


@pytest.mark.parametrize(
    "ferramenta",
    [docstring.listar_instancias, modelo_pydantic.listar_instancias],
    ids=["forma2", "forma4"],
)
def test_estado_fora_do_enum(ferramenta):
    with pytest.raises(ValidationError):
        ferramenta.invoke({"estado": "parado"})


def test_pedido_de_chamada_invalido_nao_vira_mensagem():
    # A ferramenta lança a exceção; quem a transforma em mensagem para o modelo é o agente.
    pedido = {
        "type": "tool_call",
        "name": "listar_instancias",
        "args": {"regiao": "Virginia"},
        "id": "pedido-2",
    }

    with pytest.raises(ValidationError):
        modelo_pydantic.listar_instancias.invoke(pedido)
