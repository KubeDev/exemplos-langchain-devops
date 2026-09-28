import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage

load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    raise SystemExit("Configure GOOGLE_API_KEY no arquivo .env antes de executar.")

SYSTEM_PROMPT = """
Você é um assistente de DevOps, especialista em infraestrutura, automação e práticas de desenvolvimento.
Responda de forma clara, objetiva e concisa.
"""

model = init_chat_model("google_genai:gemini-3.8-flash")


def responder(pergunta: str) -> None:
    mensagens = [SystemMessage(SYSTEM_PROMPT), HumanMessage(pergunta)]

    print(f"\nMensagens enviadas ({len(mensagens)} mensagens):")
    print(" → ".join(type(mensagem).__name__ for mensagem in mensagens))

    resposta = model.invoke(mensagens, automatic_function_calling={"disable": True})
    print(resposta.text)


def main() -> None:
    print("Chat DevOps sem memoria — linha vazia ou 'sair' encerra\n")

    while True:
        try:
            pergunta = input("Voce: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not pergunta or pergunta.lower() == "sair":
            break

        print("\nAssistente:")
        # Nada e guardado: a lista de mensagens nasce e morre dentro de responder().
        responder(pergunta)
        print()


if __name__ == "__main__":
    main()
