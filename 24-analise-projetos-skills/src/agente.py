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

# A raiz que o agente enxerga: os projetos e /skills. Nada fora dela.
RAIZ = Path(__file__).parent.parent / "workspace"
WORKSPACE = FilesystemBackend(root_dir=RAIZ, virtual_mode=True)

# Os projetos que a interface oferece: toda pasta de workspace/ que não é a de skills.
PROJETOS = sorted(p.name for p in RAIZ.iterdir() if p.is_dir() and p.name != "skills")
SKILLS = sorted(p.name for p in (RAIZ / "skills").iterdir() if p.is_dir())

model = ChatAnthropic(model=os.getenv("MODELO", "claude-haiku-5-5"))


def criar_agente(projeto: str):
    """O mesmo agente para qualquer projeto: só a pasta do system prompt muda."""
    return create_agent(
        model=model,
        system_prompt=f"Você analisa o projeto que está em /{projeto}. Leia os arquivos antes de responder.",
        middleware=[
            FilesystemMiddleware(backend=WORKSPACE, tools=["ls", "read_file", "write_file", "edit_file"]),
            SkillsMiddleware(backend=WORKSPACE, sources=["/skills/"]),
        ],
        checkpointer=InMemorySaver(),
    )
