import json

import boto3


def consultar_instancias(estado, regiao) -> str:
    print(f"Ferramenta: listar_instancias(estado={estado!r}, regiao={regiao!r})")

    filtros = [{"Name": "instance-state-name", "Values": [estado]}] if estado else []
    resposta = boto3.client("ec2", region_name=regiao).describe_instances(Filters=filtros)

    return json.dumps(resposta, default=str, ensure_ascii=False)
