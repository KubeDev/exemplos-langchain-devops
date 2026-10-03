from typing import Annotated, Literal

from langchain.tools import tool
from pydantic import BaseModel, Field

from src.ec2 import consultar_instancias

Estado = Literal["pending", "running", "stopping", "stopped", "shutting-down", "terminated"]
Regiao = Annotated[str, Field(pattern=r"^[a-z]{2}(-[a-z]+)+-\d+$")]


class ListarInstanciasInput(BaseModel):
    estado: Estado | None = Field(
        default=None, description="Estado da instância. Sem estado, lista todas."
    )
    regiao: Regiao | None = Field(
        default=None, description="Região AWS. Sem região, usa a região padrão da aplicação."
    )


@tool(args_schema=ListarInstanciasInput)
def listar_instancias(estado: str | None = None, regiao: str | None = None) -> str:
    """Lista as instâncias EC2 da conta, com filtro opcional por estado e por região."""
    return consultar_instancias(estado, regiao)
