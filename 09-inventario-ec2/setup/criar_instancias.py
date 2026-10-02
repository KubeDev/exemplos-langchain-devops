"""Cria as instâncias de teste da aula em duas regiões.

us-east-1: web-01 rodando, worker-01 e batch-01 paradas.
us-east-2: web-02 rodando, batch-02 parada.

Usa a VPC padrão de cada região. Todas recebem a tag Projeto=inventario-ec2, que é o
que o setup/destruir_instancias.py usa para encontrá-las.

    uv run setup/criar_instancias.py
"""

import boto3
from dotenv import load_dotenv

load_dotenv()

INSTANCIAS = {
    "us-east-1": {"web-01": "running", "worker-01": "stopped", "batch-01": "stopped"},
    "us-east-2": {"web-02": "running", "batch-02": "stopped"},
}
AMI_PARAMETRO = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"


def criar_na_regiao(regiao: str, estados: dict[str, str]) -> None:
    ec2 = boto3.client("ec2", region_name=regiao)
    ssm = boto3.client("ssm", region_name=regiao)
    ami = ssm.get_parameter(Name=AMI_PARAMETRO)["Parameter"]["Value"]

    ids = {}
    for nome in estados:
        resposta = ec2.run_instances(
            ImageId=ami,
            InstanceType="t3.micro",
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Name", "Value": nome},
                        {"Key": "Projeto", "Value": "inventario-ec2"},
                    ],
                }
            ],
        )
        ids[nome] = resposta["Instances"][0]["InstanceId"]
        print(f"[{regiao}] Criada: {nome} ({ids[nome]})")

    print(f"[{regiao}] Aguardando as instâncias iniciarem...")
    ec2.get_waiter("instance_running").wait(InstanceIds=list(ids.values()))

    parar = [ids[nome] for nome, estado in estados.items() if estado == "stopped"]
    if parar:
        print(f"[{regiao}] Parando {', '.join(n for n, e in estados.items() if e == 'stopped')}...")
        ec2.stop_instances(InstanceIds=parar)
        ec2.get_waiter("instance_stopped").wait(InstanceIds=parar)

    resposta = ec2.describe_instances(InstanceIds=list(ids.values()))
    for reserva in resposta["Reservations"]:
        for instancia in reserva["Instances"]:
            tags = {tag["Key"]: tag["Value"] for tag in instancia.get("Tags", [])}
            print(
                f"[{regiao}] {instancia['InstanceId']} · "
                f"{instancia['State']['Name']} · {tags['Name']}"
            )


def main() -> None:
    for regiao, estados in INSTANCIAS.items():
        criar_na_regiao(regiao, estados)


if __name__ == "__main__":
    main()
