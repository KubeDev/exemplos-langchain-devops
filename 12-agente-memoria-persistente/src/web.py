"""Formulários, sessões e HTML do chat."""

import os
from uuid import uuid4

from flask import Flask, redirect, render_template, request, url_for
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from psycopg import OperationalError

from src.agent import respond
from src.checkpointer import BACKEND, memory_checkpointer, postgres_checkpointer

app = Flask(__name__)


def existing_threads(checkpointer: BaseCheckpointSaver) -> list[str]:
    """Lista os IDs únicos das threads que já têm checkpoints."""

    threads: list[str] = []
    for saved in checkpointer.list(None):
        thread_id = saved.config["configurable"]["thread_id"]
        if thread_id not in threads:
            threads.append(thread_id)
    return threads


def conversation(checkpointer: BaseCheckpointSaver, thread_id: str):
    """Recupera as mensagens do último checkpoint da thread."""

    saved = checkpointer.get_tuple({"configurable": {"thread_id": thread_id}})
    if saved is None:
        return []
    messages = saved.checkpoint["channel_values"].get("messages", [])
    return [message for message in messages if isinstance(message, (HumanMessage, AIMessage))]


def render_page(checkpointer: BaseCheckpointSaver, thread_id: str | None = None, error: str | None = None):
    """Renderiza o seletor de sessões e o histórico da thread escolhida."""

    threads = existing_threads(checkpointer)
    thread_id = thread_id or request.args.get("thread_id") or (threads[0] if threads else str(uuid4()))
    messages = [
        {"role": "user" if message.type == "human" else "assistant", "content": str(message.text)}
        for message in conversation(checkpointer, thread_id)
    ]
    return render_template(
        "index.html",
        backend_label="Em memória" if BACKEND == "memory" else "PostgreSQL",
        thread_id=thread_id,
        threads=threads,
        messages=messages,
        error=error,
    )


def send_message(checkpointer: BaseCheckpointSaver):
    """Envia a mensagem do formulário e volta à mesma thread."""

    thread_id = request.form.get("thread_id", "")
    prompt = request.form.get("prompt", "").strip()
    if not thread_id or not prompt:
        return redirect(url_for("chat", thread_id=thread_id))
    if not os.getenv("ANTHROPIC_API_KEY"):
        return render_page(checkpointer, thread_id, "Configure ANTHROPIC_API_KEY no arquivo .env.")

    try:
        respond(checkpointer, thread_id, prompt)
    except Exception as exc:
        app.logger.exception("Falha ao responder")
        return render_page(checkpointer, thread_id, f"A chamada falhou ({type(exc).__name__}).")
    return redirect(url_for("chat", thread_id=thread_id))


@app.route("/", methods=["GET", "POST"])
def chat():
    """Atende o chat com o backend escolhido ao iniciar o processo."""

    if request.method == "POST" and request.form.get("action") == "new":
        return redirect(url_for("chat", thread_id=str(uuid4())))

    if BACKEND == "memory":
        checkpointer = memory_checkpointer()
        return send_message(checkpointer) if request.method == "POST" else render_page(checkpointer)

    try:
        with postgres_checkpointer() as checkpointer:
            checkpointer.setup()
            return send_message(checkpointer) if request.method == "POST" else render_page(checkpointer)
    except OperationalError:
        return "PostgreSQL indisponível. Inicie o banco com docker compose up -d --wait.", 503
