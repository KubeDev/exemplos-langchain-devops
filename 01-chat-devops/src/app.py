import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage

load_dotenv()

SYSTEM_PROMPT = """
Você é um assistente de DevOps, especialista em infraestrutura, automação e práticas de desenvolvimento.
Responda sempre de forma clara e objetiva usando exemplos e analogias.
"""

# Inicializa o modelo de chat com base na variável de ambiente MODELO, ou usa um padrão se não estiver definida.
model = init_chat_model(os.getenv("MODELO", "anthropic:claude-sonnet-5"))


def responder(pergunta: str) -> None:
    """Espera a resposta inteira do modelo e imprime de uma vez."""
    resposta = model.invoke([SystemMessage(SYSTEM_PROMPT), HumanMessage(pergunta)])
    print(resposta.text)

def responder_streaming(pergunta: str) -> None:
    """Imprime a resposta pedaco a pedaco, conforme o modelo gera."""
    for chunk in model.stream([SystemMessage(SYSTEM_PROMPT), HumanMessage(pergunta)]):
        print(chunk.text, end="", flush=True)
    print()

def main() -> None:
    print("Chat DevOps — pergunte algo (linha vazia ou 'sair' para encerrar)\n")
    while True:
        try:
            pergunta = input("Voce: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not pergunta or pergunta.lower() == "sair":
            break

        print("\nAssistente:")
        responder(pergunta)
        print()


if __name__ == "__main__":
    main()







