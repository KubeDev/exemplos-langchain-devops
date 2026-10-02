from typing import Annotated, Literal

from langchain.tools import tool
from pydantic import Field

from src.ec2 import consultar_instancias

Estado = Literal["pending", "running", "stopping", "stopped", "shutting-down", "terminated"]
Regiao = Annotated[str, Field(pattern=r"^[a-z]{2}(-[a-z]+)+-\d+$")]


@tool
def listar_instancias(
    estado: Annotated[
        Estado | None, Field(description="Estado da instância. Sem estado, lista todas.")
    ] = None,
    regiao: Annotated[
        Regiao | None,
        Field(description="Região AWS. Sem região, usa a região padrão da aplicação."),
    ] = None,
) -> str:
    """Lista as instâncias EC2 da conta, com filtro opcional por estado e por região."""
    return consultar_instancias(estado, regiao)
