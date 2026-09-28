import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    raise SystemExit("Configure GOOGLE_API_KEY no arquivo .env antes de executar.")

SYSTEM_PROMPT = """
Você é um assistente de DevOps, especialista em infraestrutura, automação e práticas de desenvolvimento.
Responda de forma clara, objetiva e concisa.
"""

model = init_chat_model("google_genai:gemini-3.8-flash")

prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessage(SYSTEM_PROMPT),
        ("human", "{pergunta}"),
    ]
)


def responder(pergunta: str) -> None:
    """Compoe as mensagens a partir do template e imprime a resposta do modelo."""
    prompt_value = prompt.invoke({"pergunta": pergunta})
    mensagens = prompt_value.to_messages()

    tipos_enviados = " → ".join(type(mensagem).__name__ for mensagem in mensagens)
    print(f"\nPrompt produzido: {type(prompt_value).__name__}")
    print(f"Mensagens enviadas ({len(mensagens)} mensagens):")
    print(tipos_enviados)

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
        # O template e fixo e nao sabe nada do passado: a lista que ele produz
        # nasce e morre dentro de responder().
        responder(pergunta)
        print()


if __name__ == "__main__":
    main()
