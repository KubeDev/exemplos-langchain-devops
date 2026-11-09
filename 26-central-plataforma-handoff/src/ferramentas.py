"""Ferramentas simuladas dos dois especialistas da central.

É encanamento, fora do escopo da aula: os dados são fictícios e ficam em dicionários. O que a
aula ensina está em agente.py.
"""

import json
import math
from typing import Literal

from langchain.tools import tool

Projeto = Literal["kube-news", "encontros-tech"]

# ---------------------------------------------------------------------------
# Dados simulados
# ---------------------------------------------------------------------------

CUSTOS = {  # em dólares, por mês e por serviço
    "kube-news": {
        "2026-08": {"compute": 410.0, "banco": 180.0, "gpu": 0.0, "rede": 45.0},
        "2026-09": {"compute": 425.0, "banco": 185.0, "gpu": 0.0, "rede": 47.0},
        "2026-10": {"compute": 430.0, "banco": 190.0, "gpu": 1240.0, "rede": 48.0},
    },
    "encontros-tech": {
        "2026-08": {"compute": 220.0, "banco": 95.0, "gpu": 0.0, "rede": 20.0},
        "2026-09": {"compute": 225.0, "banco": 95.0, "gpu": 0.0, "rede": 21.0},
        "2026-10": {"compute": 230.0, "banco": 98.0, "gpu": 0.0, "rede": 22.0},
    },
}

RECURSOS_OCIOSOS = {
    "kube-news": [
        {
            "recurso": "node pool gpu-staging (2 nós)",
            "ambiente": "staging",
            "custo_mensal": 1240.0,
            "uso_medio_cpu": "2%",
            "criado_em": "2026-10-03",
        },
    ],
    "encontros-tech": [],
}

USO_ATUAL = {
    "kube-news": {
        "replicas": 3,
        "hpa_max": 6,
        "requisicoes_por_segundo": 120,
        "cpu_por_replica": "62%",
        "conexoes_banco_em_uso": 70,
        "conexoes_banco_max": 100,
    },
    "encontros-tech": {
        "replicas": 2,
        "hpa_max": 8,
        "requisicoes_por_segundo": 40,
        "cpu_por_replica": "35%",
        "conexoes_banco_em_uso": 20,
        "conexoes_banco_max": 100,
    },
}

PICO_HISTORICO = {
    "kube-news": {"evento": "campanha de junho", "requisicoes_por_segundo": 260, "replicas_usadas": 6},
    "encontros-tech": {"evento": "inscrições do meetup anual", "requisicoes_por_segundo": 90, "replicas_usadas": 3},
}

REQUISICOES_POR_REPLICA = 50  # o que uma réplica atende com folga


# ---------------------------------------------------------------------------
# Ferramentas de FinOps
# ---------------------------------------------------------------------------


@tool
def custos_por_servico(projeto: Projeto) -> str:
    """Custo mensal do projeto por serviço nos últimos três meses, em dólares (USD)."""
    return json.dumps(CUSTOS[projeto], ensure_ascii=False)


@tool
def recursos_ociosos(projeto: Projeto) -> str:
    """Recursos do projeto com uso muito baixo, com custo mensal em dólares (USD) e data de criação."""
    return json.dumps(RECURSOS_OCIOSOS[projeto], ensure_ascii=False)


@tool
def estimar_custo_adicional(projeto: Projeto, replicas_extras: int) -> str:
    """Custo mensal a mais, em dólares (USD), para rodar réplicas além das que rodam hoje."""
    uso = USO_ATUAL[projeto]
    compute_atual = CUSTOS[projeto]["2026-10"]["compute"]
    por_replica = compute_atual / uso["replicas"]
    return json.dumps(
        {
            "custo_por_replica": round(por_replica, 2),
            "replicas_extras": replicas_extras,
            "custo_mensal_adicional": round(por_replica * replicas_extras, 2),
        },
        ensure_ascii=False,
    )


# ---------------------------------------------------------------------------
# Ferramentas de Capacidade
# ---------------------------------------------------------------------------


@tool
def uso_atual(projeto: Projeto) -> str:
    """Réplicas, limite do HPA, requisições por segundo e conexões de banco do projeto agora."""
    return json.dumps(USO_ATUAL[projeto], ensure_ascii=False)


@tool
def historico_pico(projeto: Projeto) -> str:
    """O maior pico de tráfego já atendido pelo projeto."""
    return json.dumps(PICO_HISTORICO[projeto], ensure_ascii=False)


@tool
def projetar_capacidade(projeto: Projeto, multiplicador: float) -> str:
    """Projeta réplicas e conexões de banco para o tráfego atual multiplicado, e aponta gargalos."""
    uso = USO_ATUAL[projeto]
    requisicoes = uso["requisicoes_por_segundo"] * multiplicador
    replicas = math.ceil(requisicoes / REQUISICOES_POR_REPLICA)
    conexoes = math.ceil(uso["conexoes_banco_em_uso"] * multiplicador)
    gargalos = []
    if replicas > uso["hpa_max"]:
        gargalos.append(f"HPA limitado a {uso['hpa_max']} réplicas, precisa de {replicas}")
    if conexoes > uso["conexoes_banco_max"]:
        gargalos.append(f"banco limitado a {uso['conexoes_banco_max']} conexões, precisa de {conexoes}")
    return json.dumps(
        {
            "requisicoes_por_segundo": requisicoes,
            "replicas_atuais": uso["replicas"],
            "replicas_necessarias": replicas,
            "conexoes_banco_necessarias": conexoes,
            "gargalos": gargalos,
        },
        ensure_ascii=False,
    )


FERRAMENTAS_FINOPS = [custos_por_servico, recursos_ociosos, estimar_custo_adicional]
FERRAMENTAS_CAPACIDADE = [uso_atual, historico_pico, projetar_capacidade]
