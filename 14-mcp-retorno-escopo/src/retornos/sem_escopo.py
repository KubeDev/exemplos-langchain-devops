import json

from fastmcp.tools import ToolResult


def retornar(itens: list[dict], escopo: dict) -> ToolResult:
    # Só os itens: o recorte aplicado pelo server fica de fora.
    # Para quem lê, uma lista vazia significa "não existe".
    return ToolResult(content=json.dumps(itens, ensure_ascii=False))
