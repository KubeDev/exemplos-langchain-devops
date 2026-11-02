from langchain.agents.middleware import AgentMiddleware
from langchain.messages import ToolMessage

from src.ferramentas import MAQUINAS


def janela_aberta(arquivo: str) -> bool:
    """A janela só está aberta se o arquivo disser "aberta". Sem arquivo, está fechada."""
    try:
        with open(arquivo) as f:
            return f.read().strip() == "aberta"
    except OSError:
        return False


def verificar(tool_call: dict, tag: str, aberta: bool) -> str | None:
    """A regra do time: devolve o motivo do bloqueio, ou None se a chamada pode seguir."""
    if tool_call["name"] != "desligar_maquinas" or aberta:
        return None

    protegidas = [
        nome for nome in tool_call["args"].get("nomes", [])
        if tag in MAQUINAS.get(nome, {}).get("tags", [])
    ]
    if not protegidas:
        return None

    return (
        f"Bloqueado pela política de manutenção: {', '.join(protegidas)} tem a tag {tag} "
        "e a janela de manutenção está fechada. Execute só quando a janela estiver aberta."
    )


class GuardrailManutencao(AgentMiddleware):
    """Barra o desligamento de máquina com a tag protegida fora da janela de manutenção."""

    def __init__(self, tag: str, arquivo: str):
        super().__init__()
        self.tag = tag
        self.arquivo = arquivo

    def wrap_tool_call(self, request, handler):
        # O arquivo é lido a cada chamada: abrir ou fechar a janela vale sem reiniciar o app.
        motivo = verificar(request.tool_call, self.tag, janela_aberta(self.arquivo))

        if motivo:
            # Curto-circuito: o handler não é chamado, a ferramenta não executa.
            return ToolMessage(
                content=motivo,
                tool_call_id=request.tool_call["id"],
                name=request.tool_call["name"],
                status="error",
            )

        return handler(request)
