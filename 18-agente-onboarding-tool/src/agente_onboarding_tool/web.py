"""Interface web do exemplo: as páginas de ingestão e de chat na mesma aplicação.

É encanamento, fora do escopo da aula. Aqui ficam as rotas, a leitura dos formulários, as sessões
e a preparação do que cada página mostra. O que a aula ensina está em outros dois arquivos:

- ingestao.py: o documento vira chunks com metadado e é gravado no índice;
- agente.py: o agente consome o índice pela ferramenta de busca.

Num sistema real, ingestão e chat seriam aplicações separadas. Aqui ficam juntas para alternar
entre as duas na mesma interface.
"""

import os
from datetime import datetime

import psycopg
from flask import Flask, redirect, render_template, request, url_for
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.postgres import PostgresSaver

# Importar os dois módulos já carrega o .env.
from agente_onboarding_tool.agente import K, responder
from agente_onboarding_tool.ingestao import documentos_no_indice, gravar

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Página de ingestão
# ---------------------------------------------------------------------------


@app.route("/ingestao", methods=["GET", "POST"])
def pagina_ingestao():
    """Mostra o índice e, num POST, entrega cada arquivo enviado à ingestão."""
    resultados = []
    if request.method == "POST":
        for arquivo in request.files.getlist("arquivos"):
            resultados.append(gravar(arquivo.filename, arquivo.read().decode("utf-8")))
    return render_template("ingestao.html", resultados=resultados, documentos=documentos_no_indice())


# ---------------------------------------------------------------------------
# Página de chat: cada sessão é uma thread no checkpointer do PostgreSQL
# ---------------------------------------------------------------------------


def nova_sessao() -> str:
    """O identificador da sessão é a data e a hora em que ela começou."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def sessoes_salvas(checkpointer: BaseCheckpointSaver) -> list[str]:
    """Lista as threads gravadas, da mais recente para a mais antiga."""
    threads = {salvo.config["configurable"]["thread_id"] for salvo in checkpointer.list(None)}
    return sorted(threads, reverse=True)


def historico(checkpointer: BaseCheckpointSaver, thread_id: str) -> list[dict]:
    """Lê as mensagens da thread no checkpointer e prepara cada uma para a página."""
    salvo = checkpointer.get_tuple({"configurable": {"thread_id": thread_id}})
    if salvo is None:
        return []

    mensagens = []
    for mensagem in salvo.checkpoint["channel_values"].get("messages", []):
        if isinstance(mensagem, HumanMessage):
            mensagens.append({"papel": "user", "rotulo": "Você", "texto": mensagem.text})
        elif isinstance(mensagem, AIMessage):
            for chamada in mensagem.tool_calls:
                argumentos = ", ".join(f"{chave}={valor!r}" for chave, valor in chamada["args"].items())
                mensagens.append({"papel": "tool", "rotulo": "Agente chamou", "texto": f"{chamada['name']}({argumentos})"})
            if mensagem.text:
                mensagens.append({"papel": "assistant", "rotulo": "Assistente", "texto": mensagem.text})
        elif isinstance(mensagem, ToolMessage):
            mensagens.append({"papel": "tool", "rotulo": "Trechos devolvidos pela ferramenta", "texto": "", "detalhe": mensagem.text})
    return mensagens


@app.route("/", methods=["GET", "POST"])
def pagina_chat():
    """Mostra a sessão escolhida; num POST, cria uma sessão nova ou entrega a pergunta ao agente."""
    if request.method == "POST" and request.form.get("acao") == "nova":
        return redirect(url_for("pagina_chat", thread_id=nova_sessao()))

    with PostgresSaver.from_conn_string(os.environ["DATABASE_URL"]) as checkpointer:
        checkpointer.setup()

        if request.method == "POST":
            thread_id = request.form["thread_id"]
            pergunta = request.form.get("pergunta", "").strip()
            if pergunta:
                responder(pergunta, thread_id, checkpointer)
            return redirect(url_for("pagina_chat", thread_id=thread_id))

        sessoes = sessoes_salvas(checkpointer)
        thread_id = request.args.get("thread_id") or (sessoes[0] if sessoes else nova_sessao())
        return render_template(
            "chat.html",
            k=K,
            sessoes=sessoes,
            thread_id=thread_id,
            mensagens=historico(checkpointer, thread_id),
        )


# ---------------------------------------------------------------------------
# Aplicação
# ---------------------------------------------------------------------------


@app.errorhandler(psycopg.OperationalError)
def banco_indisponivel(_erro):
    return "PostgreSQL indisponível. Inicie o banco com docker compose up -d --wait.", 503


def main() -> None:
    app.run(host="127.0.0.1", port=8003)
