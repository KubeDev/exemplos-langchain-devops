import json
import os
import time

from pydo import Client

JANELA_SEGUNDOS = 10 * 60


def consultar_saude(regiao) -> str:
    print(f"Ferramenta: verificar_saude(regiao={regiao!r})")

    cliente = Client(token=os.environ["DIGITALOCEAN_TOKEN"])
    droplets = cliente.droplets.list()["droplets"]

    if regiao:
        droplets = [d for d in droplets if d["region"]["slug"] == regiao]

    fim = int(time.time())
    inicio = fim - JANELA_SEGUNDOS

    saude = {}
    for droplet in droplets:
        saude[droplet["name"]] = cliente.monitoring.get_droplet_load1_metrics(
            host_id=str(droplet["id"]), start=str(inicio), end=str(fim)
        )

    return json.dumps(saude, ensure_ascii=False)
