"""Interface web. Só lê a pausa do agente e devolve a decisão; o fluxo está em agente.py."""

import uuid

import streamlit as st
from langchain.messages import AIMessage, ToolMessage

from src.agente import executar, retomar
from src.ferramentas import MAQUINAS

ROTULOS = {"approve": "Aprovar", "edit": "Editar", "reject": "Rejeitar"}

st.set_page_config(page_title="Operação de máquinas", layout="wide")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.conversa = []
    st.session_state.pausa = None
    st.session_state.mensagens = []


def guardar(resultado: dict) -> None:
    st.session_state.mensagens = resultado["mensagens"]
    st.session_state.pausa = resultado.get("pausa")
    st.session_state.pausa_id = resultado.get("pausa_id")
    if "resposta" in resultado:
        st.session_state.conversa.append(("assistant", resultado["resposta"]))


with st.sidebar:
    st.header("Máquinas")
    st.dataframe(
        [{"nome": nome, "ambiente": m["ambiente"], "status": m["status"]}
         for nome, m in MAQUINAS.items()],
        hide_index=True,
    )
    if st.button("Nova conversa"):
        del st.session_state.thread_id
        st.rerun()

st.title("Operação de máquinas")

for papel, texto in st.session_state.conversa:
    with st.chat_message(papel):
        st.markdown(texto)

with st.expander("Chamadas de ferramenta"):
    for mensagem in st.session_state.mensagens:
        if isinstance(mensagem, AIMessage):
            for chamada in mensagem.tool_calls:
                st.code(f"[model] chama {chamada['name']}({chamada['args']})", language=None, wrap_lines=True)
        elif isinstance(mensagem, ToolMessage):
            st.code(f"[{mensagem.name}]\n{mensagem.content}", language=None, wrap_lines=True)

pausa = st.session_state.pausa

if pausa:
    st.subheader("Aprovação necessária")
    configs = {c["action_name"]: c for c in pausa["review_configs"]}
    decisoes = []
    for i, acao in enumerate(pausa["action_requests"]):
        chave = f"{st.session_state.pausa_id}-{i}"
        with st.container(border=True):
            st.code(acao["description"], language=None)
            permitidas = configs[acao["name"]]["allowed_decisions"]
            escolha = st.radio(
                "Decisão", permitidas, format_func=ROTULOS.get, horizontal=True, key=f"d-{chave}"
            )
            if escolha == "approve":
                decisoes.append({"type": "approve"})
            elif escolha == "edit":
                nomes = st.multiselect(
                    "Máquinas", list(MAQUINAS), default=acao["args"]["nomes"], key=f"e-{chave}"
                )
                decisoes.append(
                    {"type": "edit", "edited_action": {"name": acao["name"], "args": {"nomes": nomes}}}
                )
            else:
                motivo = st.text_input("Motivo", key=f"r-{chave}")
                decisoes.append({"type": "reject", "message": motivo} if motivo else {"type": "reject"})

    # O clique devolve as decisões ao agente: retomar() monta o Command(resume=...) na mesma thread.
    if st.button("Enviar decisões", type="primary"):
        with st.spinner("Retomando..."):
            guardar(retomar(decisoes, st.session_state.thread_id))
        st.rerun()

elif pergunta := st.chat_input("Peça algo sobre as máquinas"):
    st.session_state.conversa.append(("user", pergunta))
    with st.spinner("Executando..."):
        guardar(executar(pergunta, st.session_state.thread_id))
    st.rerun()
