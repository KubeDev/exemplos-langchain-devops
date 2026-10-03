import json

from langchain.messages import ToolMessage

from src.ferramentas.modelo_pydantic import listar_instancias


def nomes(resultado: str) -> set[str]:
    resposta = json.loads(resultado)
    return {
        tag["Value"]
        for reserva in resposta["Reservations"]
        for instancia in reserva["Instances"]
        for tag in instancia.get("Tags", [])
        if tag["Key"] == "Name"
    }


def test_invoke_com_argumentos():
    # O teste no lugar da aplicação: executa a ferramenta com os argumentos.
    resultado = listar_instancias.invoke({"estado": "stopped"})

    assert {"worker-01", "batch-01"} <= nomes(resultado)
    assert "web-01" not in nomes(resultado)


def test_invoke_com_regiao():
    resultado = listar_instancias.invoke({"estado": "stopped", "regiao": "us-east-2"})

    assert "batch-02" in nomes(resultado)
    assert "worker-01" not in nomes(resultado)


def test_invoke_com_pedido_de_chamada():
    # O teste no lugar do modelo: escreve à mão o pedido que ele faria.
    pedido = {
        "type": "tool_call",
        "name": "listar_instancias",
        "args": {"estado": "stopped"},
        "id": "pedido-1",
    }

    mensagem = listar_instancias.invoke(pedido)

    assert isinstance(mensagem, ToolMessage)
    assert mensagem.tool_call_id == "pedido-1"
    assert mensagem.status == "success"
    assert {"worker-01", "batch-01"} <= nomes(mensagem.content)
