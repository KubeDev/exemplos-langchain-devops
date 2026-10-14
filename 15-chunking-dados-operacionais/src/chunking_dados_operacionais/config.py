"""Configuração compartilhada pelos comandos do exemplo."""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "dados"
PERGUNTAS = ROOT / "perguntas.json"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def colecao(configuracao: str) -> str:
    """Cada configuração de chunk fica numa coleção própria."""
    return f"chunks_{configuracao}"


def database_url() -> str:
    """Lê a conexão PostgreSQL do ambiente do exemplo."""
    load_dotenv(ROOT / ".env")
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit("Defina DATABASE_URL no .env antes de continuar.")
    return url


def embeddings() -> OpenAIEmbeddings:
    """Cria o mesmo modelo de embedding para indexação e consulta."""
    load_dotenv(ROOT / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Defina OPENAI_API_KEY no .env antes de continuar.")
    return OpenAIEmbeddings(model=EMBEDDING_MODEL, dimensions=EMBEDDING_DIMENSIONS)


def sqlalchemy_url(url: str) -> str:
    """Seleciona o driver psycopg usado pela integração do LangChain."""
    return url.replace("postgresql://", "postgresql+psycopg://", 1)
