"""Apaga os Droplets criados pelo setup/criar_droplets.py, em todas as regiões.

Só toca em Droplets com a tag inventario-droplets. A busca é pela tag, não pela região.

Usa DIGITALOCEAN_TOKEN_SETUP, um token com escopo de escrita, separado do token do exemplo.

    uv run setup/destruir_droplets.py
"""

import os

from dotenv import load_dotenv
from pydo import Client

load_dotenv()

TAG_PROJETO = "inventario-droplets"


def main() -> None:
    cliente = Client(token=os.environ["DIGITALOCEAN_TOKEN_SETUP"])

    droplets = cliente.droplets.list(tag_name=TAG_PROJETO)["droplets"]
    if not droplets:
        print(f"Nenhum Droplet com a tag {TAG_PROJETO} encontrado.")
        return

    print(f"Apagando, em todas as regiões, os Droplets com a tag {TAG_PROJETO}:")
    for droplet in droplets:
        print(f"[{droplet['region']['slug']}] {droplet['name']} ({droplet['id']})")
    cliente.droplets.destroy_by_tag(tag_name=TAG_PROJETO)
    print("Droplets apagados.")


if __name__ == "__main__":
    main()
