import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_community.document_loaders import TextLoader
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("Configure ANTHROPIC_API_KEY no arquivo .env antes de executar.")

RUNBOOK_PATH = Path(__file__).resolve().parent.parent / "dados" / "runbook.md"
RUNBOOK_ID = "RB-274"
PERGUNTA = (
    "Segundo o runbook RB-274, qual é o procedimento para estabilizar a catalog-api "
    "quando o alerta OPS-4821 dispara?"
)

SYSTEM_PROMPT = """
Você é um agente de operações responsável por orientar a resposta a incidentes.
Responda somente com informações presentes no CONTEXTO EXTERNO abaixo.
Se o contexto não contiver o procedimento pedido, diga que não encontrou essa informação.

CONTEXTO EXTERNO:
{contexto}
"""

model = ChatAnthropic(model=os.getenv("MODELO", "claude-sonnet-5"))
agent = create_agent(model=model, tools=[])

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("historico"),
        ("human", "{pergunta}"),
    ]
)


def carregar_documento() -> str:
    loader = TextLoader(RUNBOOK_PATH, encoding="utf-8")
    documentos = loader.load()

    print(f"loader.load() devolveu {len(documentos)} Document")
    for documento in documentos:
        print(f"Conteúdo: {len(documento.page_content)} caracteres")
        print(f"Metadados: {documento.metadata}")

    return "\n\n".join(documento.page_content for documento in documentos)


def main() -> None:
    contexto = ""
    # contexto = carregar_documento()

    historico = []
    mensagens = prompt.invoke(
        {"contexto": contexto, "historico": historico, "pergunta": PERGUNTA}
    ).to_messages()

    print("Primeiro agente e conhecimento externo")
    print("Mensagens enviadas: " + " → ".join(type(m).__name__ for m in mensagens))
    runbook_presente = RUNBOOK_ID in str(mensagens[0].content)
    print(f"{RUNBOOK_ID} presente na mensagem de sistema: {runbook_presente}")
    print("\nResposta:")

    resultado = agent.invoke({"messages": mensagens})
    print(resultado["messages"][-1].text)


if __name__ == "__main__":
    main()
