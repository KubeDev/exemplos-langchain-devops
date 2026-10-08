import json
import os

from pydo import Client


def resumir(droplet) -> dict:
    ip_publico = next(
        (rede["ip_address"] for rede in droplet["networks"]["v4"] if rede["type"] == "public"),
        None,
    )
    return {
        "id": droplet["id"],
        "nome": droplet["name"],
        "status": droplet["status"],
        "regiao": droplet["region"]["slug"],
        "tamanho": droplet["size_slug"],
        "vcpus": droplet["vcpus"],
        "memoria_mb": droplet["memory"],
        "disco_gb": droplet["disk"],
        "ip_publico": ip_publico,
        "tags": droplet["tags"],
        "criado_em": droplet["created_at"],
    }


def consultar_droplets(regiao, status, memoria_minima_mb, memoria_maxima_mb) -> str:
    print(
        f"Ferramenta: listar_droplets(regiao={regiao!r}, status={status!r}, "
        f"memoria_minima_mb={memoria_minima_mb!r}, memoria_maxima_mb={memoria_maxima_mb!r})"
    )

    cliente = Client(token=os.environ["DIGITALOCEAN_TOKEN"])
    droplets = cliente.droplets.list()["droplets"]

    # A API não filtra por esses campos: o filtro é feito aqui.
    if regiao:
        droplets = [d for d in droplets if d["region"]["slug"] == regiao]
    if status:
        droplets = [d for d in droplets if d["status"] == status]
    if memoria_minima_mb is not None:
        droplets = [d for d in droplets if d["memory"] >= memoria_minima_mb]
    if memoria_maxima_mb is not None:
        droplets = [d for d in droplets if d["memory"] <= memoria_maxima_mb]

    return json.dumps([resumir(d) for d in droplets], ensure_ascii=False)
