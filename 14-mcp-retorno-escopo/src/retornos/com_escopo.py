import json

from fastmcp.tools import ToolResult


def retornar(itens: list[dict], escopo: dict) -> ToolResult:
    # O escopo vai no texto, porque é o texto que o modelo lê.
    # O conteúdo estruturado serve a clientes que leem dados; no LangChain ele vira artefato.
    linhas = [f"{chave}: {valor}" for chave, valor in escopo.items()]
    texto = (
        "Escopo da consulta\n"
        + "\n".join(linhas)
        + "\n\nResultado\n"
        + json.dumps(itens, ensure_ascii=False, indent=2)
    )

    return ToolResult(content=texto, structured_content={"escopo": escopo, "itens": itens})
