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
    resposta = model.invoke(
        [SystemMessage(SYSTEM_PROMPT), HumanMessage(pergunta)],
        automatic_function_calling={"disable": True},
    )
    print(resposta.text)
    print(f"\nTipo: {type(resposta).__name__}")
    print(f"Uso: {resposta.usage_metadata}")
    print(f"Metadados: {resposta.response_metadata}")


def responder_streaming(pergunta: str) -> None:
    for chunk in model.stream(
        [SystemMessage(SYSTEM_PROMPT), HumanMessage(pergunta)],
        automatic_function_calling={"disable": True},
    ):
        print(chunk.text, end="", flush=True)
    print()


pergunta = "Qual comando mostra o espaço em disco disponível no Linux? Responda em uma frase."

responder(pergunta)
# responder_streaming(pergunta)
