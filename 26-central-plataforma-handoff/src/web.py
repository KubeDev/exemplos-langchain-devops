"""Interface web. Mostra quem respondeu cada mensagem e o estado da thread; o fluxo está em agente.py."""

import uuid

import streamlit as st
from langchain.messages import AIMessage, ToolMessage

from src.agente import IDENTIDADES, NOMES, agent, responder

AVATARES = {"triagem": "🛎️", "finops": "💰", "capacidade": "📈"}

st.set_page_config(page_title="Central da plataforma", layout="wide")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.conversa = []  # (agente, texto); agente "usuario" para quem pergunta
    st.session_state.cadeia = ["triagem"]
    st.session_state.mensagens = []


def guardar(resultado: dict) -> None:
    """Rotula cada resposta com o especialista ativo naquele ponto do turno."""
    st.session_state.mensagens = resultado["mensagens"]
    atual = resultado["agente_inicial"]
    for mensagem in resultado["mensagens"]:
        if isinstance(mensagem, ToolMessage) and mensagem.name.startswith("transferir_para_"):
            atual = mensagem.name.removeprefix("transferir_para_")
            st.session_state.cadeia.append(atual)
            st.session_state.conversa.append(("transferencia", f"Transferido para {NOMES[atual]}"))
        elif isinstance(mensagem, AIMessage) and mensagem.text:
            st.session_state.conversa.append((atual, mensagem.text))


estado = agent.get_state({"configurable": {"thread_id": st.session_state.thread_id}}).values
ativo = estado.get("agente_ativo")
identidade = ativo or "triagem"

with st.sidebar:
    st.header("Estado da thread")
    st.metric("agente_ativo", ativo or "vazio")
    st.caption(f"Atende: {NOMES[identidade]}" + ("" if ativo else " (padrão com o campo vazio)"))
    st.subheader("Transferências da thread")
    st.code(" → ".join(NOMES[a] for a in st.session_state.cadeia), language=None, wrap_lines=True)
    st.subheader("Ferramentas visíveis ao modelo")
    for ferramenta in IDENTIDADES[identidade]["ferramentas"]:
        st.code(ferramenta.name, language=None)
    if st.button("Nova conversa"):
        del st.session_state.thread_id
        st.rerun()

st.title("Central da plataforma")

for agente, texto in st.session_state.conversa:
    if agente == "usuario":
        with st.chat_message("user"):
            st.markdown(texto)
    elif agente == "transferencia":
        st.info(texto, icon="🔀")
    else:
        with st.chat_message(NOMES[agente], avatar=AVATARES[agente]):
            st.caption(NOMES[agente])
            st.markdown(texto)

with st.expander("Chamadas de ferramenta do último turno"):
    for mensagem in st.session_state.mensagens:
        if isinstance(mensagem, AIMessage):
            for chamada in mensagem.tool_calls:
                st.code(f"[model] chama {chamada['name']}({chamada['args']})", language=None, wrap_lines=True)
        elif isinstance(mensagem, ToolMessage):
            st.code(f"[{mensagem.name}]\n{mensagem.content}", language=None, wrap_lines=True)

if pergunta := st.chat_input("Pergunte à central"):
    st.session_state.conversa.append(("usuario", pergunta))
    with st.spinner("Atendendo..."):
        guardar(responder(pergunta, st.session_state.thread_id))
    st.rerun()
