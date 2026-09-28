import os

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("Configure ANTHROPIC_API_KEY no arquivo .env antes de executar.")

SYSTEM_PROMPT = """
Você é um assistente de DevOps, especialista em infraestrutura, automação e práticas de desenvolvimento.
Responda de forma clara, objetiva e concisa.
"""

model = ChatAnthropic(model=os.getenv("MODELO", "claude-sonnet-5"))

prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessage(SYSTEM_PROMPT),
        MessagesPlaceholder("historico"),
        ("human", "{pergunta}"),
    ]
)


def novo_historico() -> list:
    """Comeca uma conversa do zero, sem mensagens anteriores."""
    return []


def responder(historico: list, pergunta: str) -> AIMessage:
    """Compoe as mensagens, imprime a entrada e devolve a resposta do modelo.

    Nao mexe no historico: quem anexa e o main().
    """
    prompt_value = prompt.invoke({"historico": historico, "pergunta": pergunta})
    mensagens = prompt_value.to_messages()

    tipos_historico = " → ".join(type(mensagem).__name__ for mensagem in historico)
    print(f"\nHistorico armazenado ({len(historico)} mensagens):")
    print(tipos_historico or "vazio")

    tipos_enviados = " → ".join(type(mensagem).__name__ for mensagem in mensagens)
    print(f"Prompt produzido: {type(prompt_value).__name__}")
    print(f"Mensagens enviadas ({len(mensagens)} mensagens):")
    print(tipos_enviados)

    resposta = model.invoke(mensagens)
    print(resposta.text)
    return resposta


def main() -> None:
    print("Chat DevOps com memoria — 'limpar' esquece tudo, linha vazia ou 'sair' encerra\n")

    historico = novo_historico()

    while True:
        try:
            pergunta = input("Voce: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not pergunta or pergunta.lower() == "sair":
            break

        if pergunta.lower() == "limpar":
            historico = novo_historico()
            print("\n[historico apagado — o modelo nao lembra mais de nada]\n")
            continue

        print("\nAssistente:")
        resposta = responder(historico, pergunta)

        # A memoria e isto: pergunta e resposta entram na lista para o proximo turno.
        historico.append(HumanMessage(pergunta))
        historico.append(resposta)
        print()


if __name__ == "__main__":
    main()
