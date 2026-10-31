import argparse

from langchain.messages import AIMessage, HumanMessage, ToolMessage

from src.agente import agent


def mostrar_chamadas(mensagem) -> None:
    if isinstance(mensagem, AIMessage):
        for chamada in mensagem.tool_calls:
            print(f"[model] chama {chamada['name']}({chamada['args']})")


def imprimir_historico(mensagens) -> None:
    print("\n===== Histórico (o estado do agente ao fim da execução) =====")
    for mensagem in mensagens:
        if isinstance(mensagem, HumanMessage):
            print(f"\n[usuário]\n{mensagem.text}")
        elif isinstance(mensagem, ToolMessage):
            print(f"\n[ferramenta]\n{mensagem.content}")
        elif isinstance(mensagem, AIMessage) and mensagem.text:
            print(f"\n[output]\n{mensagem.text}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assistente de operação com guardrail de dados sensíveis."
    )
    parser.add_argument("pergunta", help='Ex.: "Como a kube-news se conecta ao banco?"')
    args = parser.parse_args()

    print(f"Pergunta: {args.pergunta}\n")

    vistas = set()
    for estado in agent.stream({"messages": [("human", args.pergunta)]}, stream_mode="values"):
        ultima = estado["messages"][-1]
        if ultima.id not in vistas:
            vistas.add(ultima.id)
            mostrar_chamadas(ultima)

    imprimir_historico(estado["messages"])


if __name__ == "__main__":
    main()
