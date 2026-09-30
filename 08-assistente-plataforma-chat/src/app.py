import os
import sys

import streamlit as st
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.mcp import MCPAdapter
from langchain_anthropic import ChatAnthropic

from src.chat import stream_agent_text
from src.tools import mcp_config

load_dotenv()

SYSTEM_PROMPT = """
Você é um assistente de plataforma que consulta o estado do Kubernetes usando as ferramentas
disponíveis. Nunca altere recursos, consulte Secrets ou revele credenciais. Se uma informação não
estiver disponível, diga que não sabe. Considere o histórico da conversa ao interpretar referências
como "eles", "o anterior" e "esse namespace".
"""


async def responder(messages: list[dict[str, str]]):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Configure ANTHROPIC_API_KEY no arquivo .env antes de executar.")

    model = ChatAnthropic(model=os.getenv("MODELO", "claude-sonnet-5"))

    async with MCPAdapter(mcp_config()) as adapter:
        tools = await adapter.list_tools()

        print("Ferramentas MCP disponíveis:", flush=True)
        for tool in tools:
            print(f"- {tool.name}", flush=True)

        agent = create_agent(model=model, tools=tools, system_prompt=SYSTEM_PROMPT)

        async for text in stream_agent_text(agent, messages):
            yield text


if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Pergunte sobre o cluster Kubernetes"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            answer = st.write_stream(responder(st.session_state.messages))
        except Exception as error:
            print(
                f"[aplicação] falha ao responder: {type(error).__name__}",
                file=sys.stderr,
                flush=True,
            )
            answer = "Não foi possível consultar o cluster. Verifique o terminal da aplicação."
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
