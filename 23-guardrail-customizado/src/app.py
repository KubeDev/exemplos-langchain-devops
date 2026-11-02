import uuid

from langchain.messages import AIMessage, ToolMessage
from langgraph.types import Command

from src.agente import agent
from src.ferramentas import MAQUINAS


def pedir_decisoes(pausa) -> list[dict]:
    """Mostra cada ação pendente e devolve uma decisão por ação, na mesma ordem."""
    decisoes = []
    for acao in pausa["action_requests"]:
        print(f"\n[aprovação] {acao['name']}({acao['args']})")
        resposta = input("aprovar? [s/n] ").strip().lower()
        decisoes.append({"type": "approve"} if resposta == "s" else {"type": "reject"})
    return decisoes


def mostrar(mensagens) -> None:
    for mensagem in mensagens:
        if isinstance(mensagem, AIMessage):
            for chamada in mensagem.tool_calls:
                print(f"[model] chama {chamada['name']}({chamada['args']})")
            if mensagem.text:
                print(f"\n[agente]\n{mensagem.text}")
        elif isinstance(mensagem, ToolMessage):
            print(f"[{mensagem.name}] ({mensagem.status})\n{mensagem.content}")


def main() -> None:
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    print("Assistente de operação. Enter vazio encerra.")

    while pergunta := input("\nVocê: ").strip():
        inicio = len(agent.get_state(config).values.get("messages", []))
        resultado = agent.invoke({"messages": [("human", pergunta)]}, config)

        while resultado.get("__interrupt__"):
            decisoes = pedir_decisoes(resultado["__interrupt__"][0].value)
            resultado = agent.invoke(Command(resume={"decisions": decisoes}), config)

        mostrar(resultado["messages"][inicio + 1:])
        print("\n[máquinas] " + " · ".join(f"{n} {m['status']}" for n, m in MAQUINAS.items()))


if __name__ == "__main__":
    main()
