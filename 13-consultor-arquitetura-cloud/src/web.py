"""Interface web do consultor de arquitetura Cloud com dois perfis de demonstração."""

import os
from uuid import uuid4

from flask import Flask, redirect, render_template, request, url_for
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.base import BaseStore
from psycopg import OperationalError

from src.agent import respond
from src.database import open_checkpointer, open_store

app = Flask(__name__)
USERS = {"ana": "Ana", "bruno": "Bruno"}


def selected_user() -> str:
    """Seleciona um dos perfis didáticos a partir do formulário ou da URL."""
    user_id = request.values.get("user_id", "ana")
    return user_id if user_id in USERS else "ana"


def new_thread_id(user_id: str) -> str:
    """Cria um identificador de thread associado ao perfil de demonstração.

    Args:
        user_id: Perfil ao qual a nova conversa pertencerá.
    """
    return f"{user_id}:{uuid4()}"


def existing_threads(checkpointer: BaseCheckpointSaver, user_id: str) -> list[str]:
    """Lista somente as threads que pertencem ao perfil selecionado.

    Args:
        checkpointer: Persistência consultada para encontrar as conversas.
        user_id: Perfil cujas conversas serão listadas.
    """
    threads: list[str] = []
    for saved in checkpointer.list(None):
        thread_id = saved.config["configurable"]["thread_id"]
        if thread_id.startswith(f"{user_id}:") and thread_id not in threads:
            threads.append(thread_id)
    return threads


def conversation(checkpointer: BaseCheckpointSaver, thread_id: str) -> list[dict[str, str]]:
    """Recupera mensagens do usuário, respostas e resultados de ferramentas da thread.

    Args:
        checkpointer: Persistência que guarda o histórico da conversa.
        thread_id: Identificador da conversa a recuperar.
    """
    saved = checkpointer.get_tuple({"configurable": {"thread_id": thread_id}})
    if saved is None:
        return []
    messages = saved.checkpoint["channel_values"].get("messages", [])
    visible: list[dict[str, str]] = []
    for message in messages:
        if isinstance(message, HumanMessage):
            visible.append({"role": "user", "label": "Você", "content": message.text})
        elif isinstance(message, ToolMessage):
            visible.append({"role": "tool", "label": f"Ferramenta: {message.name}", "content": message.text})
        elif isinstance(message, AIMessage) and message.text:
            visible.append({"role": "assistant", "label": "Assistente", "content": message.text})
    return visible


def render_page(
    checkpointer: BaseCheckpointSaver,
    user_id: str,
    thread_id: str | None = None,
    error: str | None = None,
):
    """Desenha o seletor de perfis, a thread e seus resultados observáveis.

    Args:
        checkpointer: Persistência usada para listar e ler conversas.
        user_id: Perfil selecionado na página.
        thread_id: Conversa solicitada; usa a URL ou cria uma nova se ausente.
        error: Mensagem opcional de erro exibida na página.
    """
    threads = existing_threads(checkpointer, user_id)
    requested_thread = thread_id or request.args.get("thread_id", "")
    if requested_thread and requested_thread.startswith(f"{user_id}:"):
        active_thread = requested_thread
    else:
        active_thread = threads[0] if threads else new_thread_id(user_id)
    messages = conversation(checkpointer, active_thread)
    return render_template(
        "index.html",
        users=USERS,
        user_id=user_id,
        thread_id=active_thread,
        threads=threads,
        messages=messages,
        error=error,
    )


def send_message(checkpointer: BaseCheckpointSaver, store: BaseStore, user_id: str):
    """Envia o texto do formulário à thread válida do perfil selecionado.

    Args:
        checkpointer: Persistência da conversa que receberá a mensagem.
        store: Persistência de projetos disponível para as ferramentas.
        user_id: Perfil selecionado no formulário.
    """
    thread_id = request.form.get("thread_id", "")
    prompt = request.form.get("prompt", "").strip()
    if not thread_id.startswith(f"{user_id}:") or not prompt:
        return redirect(url_for("chat", user_id=user_id))
    if not os.getenv("ANTHROPIC_API_KEY"):
        return render_page(checkpointer, user_id, thread_id, "Configure ANTHROPIC_API_KEY no arquivo .env.")
    try:
        respond(checkpointer, store, user_id, thread_id, prompt)
    except Exception as exc:
        app.logger.exception("Falha ao responder")
        return render_page(checkpointer, user_id, thread_id, f"A chamada falhou ({type(exc).__name__}).")
    return redirect(url_for("chat", user_id=user_id, thread_id=thread_id))


@app.route("/", methods=["GET", "POST"])
def chat():
    """Atende o chat e compartilha a conexão PostgreSQL com os dois mecanismos."""
    user_id = selected_user()
    if request.method == "POST" and request.form.get("action") == "new":
        return redirect(url_for("chat", user_id=user_id, thread_id=new_thread_id(user_id)))
    try:
        with open_checkpointer() as checkpointer, open_store() as store:
            checkpointer.setup()
            store.setup()
            if request.method == "POST":
                return send_message(checkpointer, store, user_id)
            return render_page(checkpointer, user_id)
    except OperationalError:
        return "PostgreSQL indisponível. Inicie o banco com docker compose up -d --wait.", 503
