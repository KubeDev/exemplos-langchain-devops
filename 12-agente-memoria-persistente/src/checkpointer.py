"""Escolha do checkpointer de memória ou PostgreSQL pelo ambiente."""

import os

from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver

load_dotenv()

BACKEND = os.getenv("CHECKPOINTER_BACKEND", "memory").lower()
if BACKEND not in {"memory", "postgres"}:
    raise ValueError("CHECKPOINTER_BACKEND deve ser memory ou postgres.")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://aula:aula@localhost:55432/memoria")

# Compartilhado pelas requisições deste processo; um restart cria outro saver vazio.
memory_saver = InMemorySaver()


def memory_checkpointer():
    """Devolve o saver que preserva threads enquanto o processo vive."""

    return memory_saver


def postgres_checkpointer():
    """Fornece o contexto de conexão do checkpointer PostgreSQL."""

    return PostgresSaver.from_conn_string(DATABASE_URL)
