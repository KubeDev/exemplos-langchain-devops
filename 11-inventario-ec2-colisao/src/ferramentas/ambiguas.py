from typing import Literal

from langchain.tools import tool

from src.ec2 import consultar_instancias, consultar_status

Estado = Literal["pending", "running", "stopping", "stopped", "shutting-down", "terminated"]


@tool(parse_docstring=True)
def listar_instancias(estado: Estado | None = None, regiao: str | None = None) -> str:
    """Consulta as instâncias EC2 da conta.

    Args:
        estado: Estado da instância. Sem estado, considera todas.
        regiao: Região AWS no formato us-east-1. Sem região, usa a região padrão da aplicação.
    """
    return consultar_instancias(estado, regiao)


@tool(parse_docstring=True)
def verificar_status(estado: Estado | None = None, regiao: str | None = None) -> str:
    """Consulta o status das instâncias EC2 da conta.

    Args:
        estado: Estado da instância. Sem estado, considera todas.
        regiao: Região AWS no formato us-east-1. Sem região, usa a região padrão da aplicação.
    """
    return consultar_status(estado, regiao)
