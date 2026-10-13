"""Cria os Droplets de teste da aula, cobrindo os filtros da ferramenta.

Cada filtro (região, status, memória) tem um Droplet que entra e um que fica de fora.
Todos recebem a tag inventario-droplets, que é o que o setup/destruir_droplets.py usa para
encontrá-los, uma tag com a função (web, worker, batch) e o agente de Monitoring.

Droplet que já existe com o mesmo nome e a tag não é recriado; se o estado não bate com o
da tabela, o script corrige (liga ou desliga) e avisa.

Usa DIGITALOCEAN_TOKEN_SETUP, um token com escopo de escrita, separado do token do exemplo.

    uv run setup/criar_droplets.py
"""

import os
import time

from dotenv import load_dotenv
from pydo import Client

load_dotenv()

TAG_PROJETO = "inventario-droplets"
IMAGEM = "ubuntu-24-04-x64"

DROPLETS = {
    # nome:       (região, tamanho,           estado final)
    "web-01": ("nyc1", "s-1vcpu-2gb-amd", "active"),
    "worker-01": ("nyc1", "s-1vcpu-1gb-amd", "active"),
    "batch-01": ("sfo3", "s-1vcpu-1gb-amd", "off"),
}


def aguardar(cliente, droplet_id, status, tentativas=18) -> bool:
    for _ in range(tentativas):
        if cliente.droplets.get(droplet_id)["droplet"]["status"] == status:
            return True
        time.sleep(10)
    return False


def main() -> None:
    cliente = Client(token=os.environ["DIGITALOCEAN_TOKEN_SETUP"])

    existentes = {
        d["name"]: d for d in cliente.droplets.list(tag_name=TAG_PROJETO)["droplets"]
    }

    for nome, (regiao, tamanho, _) in DROPLETS.items():
        if nome in existentes:
            print(f"[{regiao}] Já existe, não recriado: {nome}")
            continue

        resposta = cliente.droplets.create(
            body={
                "name": nome,
                "region": regiao,
                "size": tamanho,
                "image": IMAGEM,
                "tags": [TAG_PROJETO, nome.split("-")[0]],
                "monitoring": True,
            }
        )
        existentes[nome] = resposta["droplet"]
        print(f"[{regiao}] Criado: {nome} ({resposta['droplet']['id']})")

    print("Aguardando os Droplets saírem do status new...")
    while any(
        cliente.droplets.get(d["id"])["droplet"]["status"] == "new" for d in existentes.values()
    ):
        time.sleep(10)

    for nome, (regiao, _, estado_final) in DROPLETS.items():
        droplet_id = existentes[nome]["id"]
        status = cliente.droplets.get(droplet_id)["droplet"]["status"]

        if status == estado_final:
            continue

        if estado_final == "off":
            print(f"[{regiao}] {nome} está {status}; desligando com shutdown...")
            cliente.droplet_actions.post(droplet_id, body={"type": "shutdown"})
            if not aguardar(cliente, droplet_id, "off"):
                # Droplet de laboratório, sem carga: forçar o desligamento não perde nada.
                print(f"[{regiao}] shutdown não concluiu; usando power_off.")
                cliente.droplet_actions.post(droplet_id, body={"type": "power_off"})
                aguardar(cliente, droplet_id, "off")
        else:
            print(f"[{regiao}] {nome} está {status}; ligando com power_on...")
            cliente.droplet_actions.post(droplet_id, body={"type": "power_on"})
            aguardar(cliente, droplet_id, "active")

    for droplet in cliente.droplets.list(tag_name=TAG_PROJETO)["droplets"]:
        print(
            f"[{droplet['region']['slug']}] {droplet['id']} · {droplet['status']} · "
            f"{droplet['name']} · {droplet['memory']} MB · {droplet['tags']}"
        )


if __name__ == "__main__":
    main()
