"""Cenário dos testes de integração: cria os Droplets antes dos casos e apaga ao final.

Setup e teardown usam DIGITALOCEAN_TOKEN_SETUP (escrita). A ferramenta testada continua com
DIGITALOCEAN_TOKEN, só de leitura. Os tokens vêm do .env.
"""

import os
import time

import pytest
from dotenv import load_dotenv
from pydo import Client

load_dotenv()

TAG = "inventario-droplets-testes"
IMAGEM = "ubuntu-24-04-x64"

CENARIO = {
    # nome:            (região, tamanho,              status final)
    "teste-web-01": ("nyc1", "s-1vcpu-1gb", "active"),
    "teste-batch-01": ("ams3", "s-1vcpu-512mb-10gb", "off"),
}


def aguardar(cliente, droplet_id, status, tentativas=30) -> bool:
    for _ in range(tentativas):
        if cliente.droplets.get(droplet_id)["droplet"]["status"] == status:
            return True
        time.sleep(10)
    return False


@pytest.fixture(scope="session")
def cenario():
    cliente = Client(token=os.environ["DIGITALOCEAN_TOKEN_SETUP"])
    try:
        ids = {}
        for nome, (regiao, tamanho, _) in CENARIO.items():
            resposta = cliente.droplets.create(
                body={"name": nome, "region": regiao, "size": tamanho, "image": IMAGEM, "tags": [TAG]}
            )
            ids[nome] = resposta["droplet"]["id"]

        for nome, (_, _, status_final) in CENARIO.items():
            assert aguardar(cliente, ids[nome], "active"), f"{nome} não ficou active"
            if status_final == "off":
                # Recém-criado, o Droplet pode ignorar o shutdown: cai para power_off.
                cliente.droplet_actions.post(ids[nome], body={"type": "shutdown"})
                if not aguardar(cliente, ids[nome], "off", tentativas=18):
                    cliente.droplet_actions.post(ids[nome], body={"type": "power_off"})
                    assert aguardar(cliente, ids[nome], "off"), f"{nome} não ficou off"

        yield CENARIO
    finally:
        # Roda mesmo com teste ou setup falhando. Só toca na tag da suíte.
        cliente.droplets.destroy_by_tag(tag_name=TAG)
