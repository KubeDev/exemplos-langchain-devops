import os
from pathlib import Path

from deepagents.backends import FilesystemBackend
from deepagents.middleware import FilesystemMiddleware, SkillsMiddleware
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("Configure ANTHROPIC_API_KEY no arquivo .env antes de executar.")

# A raiz que o agente enxerga: /projeto-analisado e /skills. Nada fora dela.
WORKSPACE = FilesystemBackend(root_dir=Path(__file__).parent.parent / "workspace", virtual_mode=True)

SYSTEM_PROMPT = """
Você analisa o projeto que está em /projeto-analisado. Leia os arquivos antes de responder.
"""

model = ChatAnthropic(model=os.getenv("MODELO", "claude-haiku-5-5"))

agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    middleware=[
        FilesystemMiddleware(backend=WORKSPACE, tools=["ls", "read_file", "write_file", "edit_file"]),
        SkillsMiddleware(backend=WORKSPACE, sources=["/skills/"]),
    ],
    checkpointer=InMemorySaver(),
)
