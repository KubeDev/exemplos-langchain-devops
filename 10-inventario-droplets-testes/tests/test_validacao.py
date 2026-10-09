# O que acontece quando o argumento quebra uma regra?
# A forma Pydantic recusa antes de executar; a forma docstring deixa passar.
# Só um teste chama a API; os demais rodam offline.

import json
import os

import pytest
from pydantic import ValidationError

from src.ferramentas import docstring, modelo_pydantic

# Aqui o skip é por teste, não pelo arquivo inteiro: só um teste precisa da API.
com_token = pytest.mark.skipif(
    not os.environ.get("DIGITALOCEAN_TOKEN"), reason="sem DIGITALOCEAN_TOKEN"
)

# Dois argumentos fora da regra: um formato (pattern) e uma regra entre campos (model_validator).
# Guardado numa variável para os mesmos dois casos rodarem nas duas formas da ferramenta.
FORA_DA_REGRA = pytest.mark.parametrize(
    "argumentos",
    [{"regiao": "NYC-1"}, {"memoria_minima_mb": 2048, "memoria_maxima_mb": 1024}],
    ids=["regiao", "minima-acima-da-maxima"],
)


@FORA_DA_REGRA
def test_pydantic_recusa_argumento_fora_da_regra(argumentos):
    # A validação barra antes de a função rodar: nada sai da máquina.
    # pytest.raises: o teste só passa se a exceção acontecer dentro do bloco.
    with pytest.raises(ValidationError):
        modelo_pydantic.listar_droplets.invoke(argumentos)


@com_token
@FORA_DA_REGRA
def test_docstring_deixa_argumento_fora_da_regra_chegar_na_execucao(argumentos):
    # Sem a regra no esquema, o valor passa, a função roda e responde sem erro.
    # Com `uv run pytest -s`, o print da ferramenta mostra a chamada indo até a API.
    resultado = docstring.listar_droplets.invoke(argumentos)

    # Uma lista vazia que parece resposta válida.
    # Para quem recebe, é igual a "não há Droplets": esse é o perigo.
    assert json.loads(resultado) == []


@pytest.mark.parametrize(
    "ferramenta",
    [docstring.listar_droplets, modelo_pydantic.listar_droplets],
    ids=["docstring", "pydantic"],
)
def test_tipo_errado_recusado_nas_duas_formas(ferramenta):
    # O tipo está no esquema das duas formas; só as regras ficaram de fora de uma.
    # O tipo vem da anotação Python (int | None), que as duas formas têm.
    with pytest.raises(ValidationError):
        ferramenta.invoke({"memoria_minima_mb": "muita"})


def test_pedido_de_chamada_invalido_nao_vira_mensagem():
    # A ferramenta lança a exceção; quem a transforma em mensagem para o modelo é o agente.
    # Mesmo recebendo um pedido de chamada, ela não devolve ToolMessage de erro.
    pedido = {
        "type": "tool_call",
        "name": "listar_droplets",
        "args": {"regiao": "NYC-1"},  # fora do pattern ^[a-z]{3}[0-9]$
        "id": "pedido-2",
    }

    with pytest.raises(ValidationError):
        modelo_pydantic.listar_droplets.invoke(pedido)
