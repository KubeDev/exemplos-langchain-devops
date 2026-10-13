"""Conexão dos dois mecanismos de persistência com o mesmo PostgreSQL."""

import os

from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://aula:aula@localhost:55433/arquitetura")


def open_checkpointer():
    """Abre um checkpointer para recuperar o histórico de cada thread."""
    return PostgresSaver.from_conn_string(DATABASE_URL)


def open_store():
    """Abre o Store para dados compartilhados entre threads de um usuário."""
    return PostgresStore.from_conn_string(DATABASE_URL)
