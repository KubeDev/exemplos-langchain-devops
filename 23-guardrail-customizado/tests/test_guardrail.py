"""A regra testada sem agente, sem modelo e sem chave de API."""

from src.guardrail import verificar


def desligar(*nomes):
    return {"name": "desligar_maquinas", "args": {"nomes": list(nomes)}, "id": "1"}


def test_prod_com_janela_fechada_e_bloqueado():
    motivo = verificar(desligar("api-01"), ambiente="prod", aberta=False)
    assert "api-01" in motivo


def test_prod_com_janela_aberta_segue():
    assert verificar(desligar("api-01"), ambiente="prod", aberta=True) is None


def test_staging_com_janela_fechada_segue():
    assert verificar(desligar("web-01"), ambiente="prod", aberta=False) is None


def test_lista_com_prod_no_meio_e_bloqueada():
    motivo = verificar(desligar("web-01", "api-01"), ambiente="prod", aberta=False)
    assert "api-01" in motivo and "web-01" not in motivo
