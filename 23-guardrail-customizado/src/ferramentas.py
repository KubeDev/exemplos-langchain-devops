from langchain.tools import tool

# Máquinas simuladas. O estado fica em memória: reiniciar o app volta ao cenário inicial.
MAQUINAS = {
    "web-01": {"tags": ["staging", "web"], "status": "active"},
    "worker-01": {"tags": ["staging", "worker"], "status": "active"},
    "api-01": {"tags": ["prod", "api"], "status": "active"},
}


@tool
def listar_maquinas() -> str:
    """Lista as máquinas com as tags e o status."""
    return "\n".join(
        f"{nome} | tags: {', '.join(m['tags'])} | {m['status']}" for nome, m in MAQUINAS.items()
    )


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


FERRAMENTAS = [listar_maquinas, desligar_maquinas]
