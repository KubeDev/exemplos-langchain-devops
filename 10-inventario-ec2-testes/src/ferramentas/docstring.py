from typing import Literal

from langchain.tools import tool

from src.ec2 import consultar_instancias

Estado = Literal["pending", "running", "stopping", "stopped", "shutting-down", "terminated"]


@tool(parse_docstring=True)
def listar_instancias(estado: Estado | None = None, regiao: str | None = None) -> str:
    """Lista as instâncias EC2 da conta, com filtro opcional por estado e por região.

    Args:
        estado: Estado da instância. Sem estado, lista todas.
        regiao: Região AWS no formato us-east-1. Sem região, usa a região padrão da aplicação.
    """
    return consultar_instancias(estado, regiao)
