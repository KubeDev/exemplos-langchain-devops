from langchain.tools import tool

# Máquinas simuladas. O estado fica em memória: reiniciar o servidor volta ao cenário inicial.
MAQUINAS = {
    "web-01": {"ambiente": "staging", "papel": "web", "status": "active",
               "cpu": "2 vCPU", "memoria": "4 GB", "disco": "80 GB", "so": "Ubuntu 24.04"},
    "web-02": {"ambiente": "staging", "papel": "web", "status": "active",
               "cpu": "2 vCPU", "memoria": "4 GB", "disco": "80 GB", "so": "Ubuntu 22.04"},
    "worker-01": {"ambiente": "staging", "papel": "worker", "status": "active",
                  "cpu": "4 vCPU", "memoria": "8 GB", "disco": "160 GB", "so": "Ubuntu 24.04"},
    "batch-01": {"ambiente": "staging", "papel": "batch", "status": "off",
                 "cpu": "8 vCPU", "memoria": "16 GB", "disco": "320 GB", "so": "Debian 12"},
    "api-01": {"ambiente": "prod", "papel": "api", "status": "active",
               "cpu": "4 vCPU", "memoria": "8 GB", "disco": "160 GB", "so": "Ubuntu 24.04"},
}


@tool
def listar_maquinas() -> str:
    """Lista as máquinas com ambiente, papel, status, hardware e sistema operacional."""
    linhas = []
    for nome, m in MAQUINAS.items():
        linhas.append(
            f"{nome} | {m['ambiente']} | {m['papel']} | {m['status']} | {m['cpu']} | "
            f"{m['memoria']} RAM | {m['disco']} disco | {m['so']}"
        )
    return "\n".join(linhas)


@tool
def ligar_maquinas(nomes: list[str]) -> str:
    """Liga as máquinas desligadas. Envie todas as máquinas numa única chamada."""
    linhas = []
    for nome in nomes:
        if nome not in MAQUINAS:
            linhas.append(f"{nome}: máquina não encontrada")
        elif MAQUINAS[nome]["status"] == "active":
            linhas.append(f"{nome}: já está active, nada a fazer")
        else:
            MAQUINAS[nome]["status"] = "active"
            linhas.append(f"{nome}: off => active")
    return "\n".join(linhas)


@tool
def desligar_maquinas(nomes: list[str]) -> str:
    """Desliga as máquinas ligadas. Envie todas as máquinas numa única chamada."""
    linhas = []
    for nome in nomes:
        if nome not in MAQUINAS:
            linhas.append(f"{nome}: máquina não encontrada")
        elif MAQUINAS[nome]["status"] == "off":
            linhas.append(f"{nome}: já está off, nada a fazer")
        else:
            MAQUINAS[nome]["status"] = "off"
            linhas.append(f"{nome}: active => off")
    return "\n".join(linhas)


@tool
def reiniciar_maquinas(nomes: list[str]) -> str:
    """Reinicia as máquinas ligadas. Envie todas as máquinas numa única chamada."""
    linhas = []
    for nome in nomes:
        if nome not in MAQUINAS:
            linhas.append(f"{nome}: máquina não encontrada")
        elif MAQUINAS[nome]["status"] == "off":
            linhas.append(f"{nome}: está off, nada a reiniciar")
        else:
            linhas.append(f"{nome}: reiniciada, active")
    return "\n".join(linhas)


FERRAMENTAS = [listar_maquinas, ligar_maquinas, desligar_maquinas, reiniciar_maquinas]
