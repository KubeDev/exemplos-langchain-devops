import uuid

from langchain.messages import AIMessage, ToolMessage

from src.agente import agent


def resumir(texto: str, linhas: int = 4) -> str:
    partes = texto.strip().splitlines()
    if len(partes) <= linhas:
        return texto.strip()
    return "\n".join(partes[:linhas]) + f"\n... ({len(partes)} linhas no histórico)"


def mostrar(mensagens) -> None:
    for mensagem in mensagens:
        if isinstance(mensagem, AIMessage):
            for chamada in mensagem.tool_calls:
                print(f"[model] chama {chamada['name']}({chamada['args']})")
            if mensagem.text:
                print(f"\n[agente]\n{mensagem.text}")
        elif isinstance(mensagem, ToolMessage):
            print(f"[{mensagem.name}]\n{resumir(mensagem.content)}")


def skills_no_historico(mensagens) -> list[str]:
    """As skills que a thread já leu: cada leitura de um SKILL.md."""
    return [
        chamada["args"]["file_path"].split("/")[-2]
        for mensagem in mensagens
        if isinstance(mensagem, AIMessage)
        for chamada in mensagem.tool_calls
        if chamada["name"] == "read_file" and chamada["args"].get("file_path", "").endswith("SKILL.md")
    ]


def main() -> None:
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    print("Análise de projeto. Enter vazio encerra.")

    while pergunta := input("\nVocê: ").strip():
        inicio = len(agent.get_state(config).values.get("messages", []))
        resultado = agent.invoke({"messages": [("human", pergunta)]}, config)

        turno = resultado["messages"][inicio + 1:]
        mostrar(turno)
        chamadas = sum(isinstance(m, AIMessage) for m in turno)
        print(f"\n[turno] chamadas de modelo: {chamadas}")
        print(
            f"[thread] mensagens: {len(resultado['messages'])} · "
            f"skills no histórico: {skills_no_historico(resultado['messages'])}"
        )


if __name__ == "__main__":
    main()
