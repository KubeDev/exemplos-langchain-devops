"""Encerra as instâncias criadas pelo setup/criar_instancias.py nas duas regiões.

Só toca em instâncias com a tag Projeto=inventario-ec2.

    uv run setup/destruir_instancias.py
"""

import boto3
from dotenv import load_dotenv

load_dotenv()

REGIOES = ["us-east-1", "us-east-2"]


def destruir_na_regiao(regiao: str) -> None:
    ec2 = boto3.client("ec2", region_name=regiao)
    resposta = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Projeto", "Values": ["inventario-ec2"]},
            {
                "Name": "instance-state-name",
                "Values": ["pending", "running", "stopping", "stopped"],
            },
        ]
    )
    ids = [i["InstanceId"] for r in resposta["Reservations"] for i in r["Instances"]]

    if not ids:
        print(f"[{regiao}] Nenhuma instância do projeto encontrada.")
        return

    print(f"[{regiao}] Encerrando: {', '.join(ids)}")
    ec2.terminate_instances(InstanceIds=ids)
    ec2.get_waiter("instance_terminated").wait(InstanceIds=ids)
    print(f"[{regiao}] Instâncias encerradas.")


def main() -> None:
    for regiao in REGIOES:
        destruir_na_regiao(regiao)


if __name__ == "__main__":
    main()
