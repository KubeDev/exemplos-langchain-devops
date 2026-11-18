"""Interface web. Escolhe o projeto, mostra cada passo do agente enquanto ele trabalha; o agente está em agente.py."""

import uuid

import streamlit as st
from langchain.messages import AIMessage, ToolMessage

from src.agente import PROJETOS, SKILLS, criar_agente

st.set_page_config(page_title="Análise de projetos", layout="wide")


@st.cache_resource
def agente(projeto: str):
    return criar_agente(projeto)


def resumir(texto: str, linhas: int = 4) -> str:
    partes = texto.strip().splitlines()
    if len(partes) <= linhas:
        return texto.strip()
    return "\n".join(partes[:linhas]) + f"\n... ({len(partes)} linhas no histórico)"


def skill_lida(chamada: dict) -> str | None:
    """O nome da skill quando a chamada é a leitura de um SKILL.md."""
    caminho = chamada["args"].get("file_path", "")
    if chamada["name"] == "read_file" and caminho.endswith("SKILL.md"):
        return caminho.split("/")[-2]
    return None


def skills_no_historico(mensagens) -> list[str]:
    """As skills que a thread já leu: cada leitura de um SKILL.md."""
    return [
        nome
        for mensagem in mensagens
        if isinstance(mensagem, AIMessage)
        for chamada in mensagem.tool_calls
        if (nome := skill_lida(chamada))
    ]


def passos(mensagem) -> list[tuple[str, str]]:
    """O que uma mensagem nova vira na tela: (tipo, texto)."""
    if isinstance(mensagem, AIMessage):
        saida = []
        for chamada in mensagem.tool_calls:
            if nome := skill_lida(chamada):
                saida.append(("skill", f"skill carregada: {nome}"))
            saida.append(("codigo", f"[model] chama {chamada['name']}({chamada['args']})"))
        return saida
    if isinstance(mensagem, ToolMessage):
        return [("codigo", f"[{mensagem.name}]\n{resumir(mensagem.content)}")]
    return []


def desenhar(tipo: str, texto: str) -> None:
    if tipo == "skill":
        st.success(texto, icon="📘")
    else:
        st.code(texto, language=None, wrap_lines=True)


def nova_conversa() -> None:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.turnos = []
    st.session_state.mensagens = []


if "thread_id" not in st.session_state:
    nova_conversa()

with st.sidebar:
    st.header("Projeto")
    # Trocar o projeto troca o agente: a conversa recomeça numa thread nova.
    projeto = st.selectbox("Pasta em workspace/", PROJETOS, on_change=nova_conversa)
    st.header("Skills")
    lidas = skills_no_historico(st.session_state.mensagens)
    for nome in SKILLS:
        st.write(f"{'✅' if nome in lidas else '▫️'} {nome}")
    st.caption("✅ = já está no histórico desta thread")
    if st.button("Nova conversa"):
        nova_conversa()
        st.rerun()

st.title(f"Análise de /{projeto}")

for turno in st.session_state.turnos:
    with st.chat_message("user"):
        st.markdown(turno["pergunta"])
    with st.chat_message("assistant"):
        with st.expander(f"Passo a passo · {turno['chamadas']} chamadas de modelo"):
            for tipo, texto in turno["passos"]:
                desenhar(tipo, texto)
        st.markdown(turno["resposta"])
        st.caption(turno["rodape"])

if pergunta := st.chat_input(f"Pergunte sobre /{projeto}"):
    with st.chat_message("user"):
        st.markdown(pergunta)

    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    turno = {"pergunta": pergunta, "passos": [], "chamadas": 0, "resposta": ""}

    with st.chat_message("assistant"):
        # stream_mode="updates": cada nó do agente (modelo ou ferramentas) entrega o que acrescentou.
        with st.status("Analisando...", expanded=True) as status:
            for atualizacao in agente(projeto).stream(
                {"messages": [("human", pergunta)]}, config, stream_mode="updates"
            ):
                for dados in atualizacao.values():
                    for mensagem in (dados or {}).get("messages", []):
                        if isinstance(mensagem, AIMessage):
                            turno["chamadas"] += 1
                            turno["resposta"] = mensagem.text
                        for tipo, texto in passos(mensagem):
                            turno["passos"].append((tipo, texto))
                            desenhar(tipo, texto)
            status.update(label=f"Concluído · {turno['chamadas']} chamadas de modelo", state="complete", expanded=False)

    st.session_state.mensagens = agente(projeto).get_state(config).values["messages"]
    turno["rodape"] = (
        f"[thread] mensagens: {len(st.session_state.mensagens)} · "
        f"skills no histórico: {skills_no_historico(st.session_state.mensagens)}"
    )
    st.session_state.turnos.append(turno)
    st.rerun()
