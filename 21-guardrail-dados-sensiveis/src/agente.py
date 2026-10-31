import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic

from src.ferramentas import consultar_aplicacao
from src.guardrails import GUARDRAILS

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("Configure ANTHROPIC_API_KEY no arquivo .env antes de executar.")

SYSTEM_PROMPT = """
Você é o assistente de operação da plataforma. Use a ferramenta consultar_aplicacao para
responder sobre a configuração e o estado das aplicações. Ao mostrar configuração, copie os
valores exatamente como a ferramenta devolveu.
Se receber uma credencial mascarada, não tente usá-la: explique que a credencial deve vir
da configuração do ambiente, nunca do chat.
"""

model = ChatAnthropic(model=os.getenv("MODELO", "claude-haiku-5-5"))

agent = create_agent(
    model=model,
    tools=[consultar_aplicacao],
    system_prompt=SYSTEM_PROMPT,
    middleware=GUARDRAILS,
)
