import os

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.messages import AIMessage, HumanMessage, SystemMessage

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("Configure ANTHROPIC_API_KEY no arquivo .env antes de executar.")

SYSTEM_PROMPT = """
Você é um assistente de DevOps, especialista em infraestrutura, automação e práticas de desenvolvimento.
Responda sempre de forma clara e objetiva usando exemplos e analogias.
"""

model = ChatAnthropic(model=os.getenv("MODELO", "claude-sonnet-5"))


def novo_historico() -> list:
    """Comeca uma conversa do zero — so com o system prompt na posicao 0."""
    return [SystemMessage(SYSTEM_PROMPT)]


def responder(historico: list) -> AIMessage:
    """Envia o historico inteiro, imprime a resposta e devolve a mensagem do modelo.

    Nao mexe no historico: quem anexa e o main().
    """
    tipos = " → ".join(type(mensagem).__name__ for mensagem in historico)
    print(f"\nContexto enviado ({len(historico)} mensagens):")
    print(tipos)

    resposta = model.invoke(historico)
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

        # A memoria e isto: a pergunta entra na lista e a lista inteira vai junto.
        historico.append(HumanMessage(pergunta))

        print("\nAssistente:")
        historico.append(responder(historico))
        print()


if __name__ == "__main__":
    main()
