from typing import Literal

from langchain.tools import tool

from src.ec2 import consultar_instancias, consultar_status

Estado = Literal["pending", "running", "stopping", "stopped", "shutting-down", "terminated"]


@tool(parse_docstring=True)
def listar_instancias(estado: Estado | None = None, regiao: str | None = None) -> str:
    """Lista as instâncias EC2 da conta com o estado de cada uma: rodando, parada, encerrada.

    Use para saber quais instâncias existem e se estão rodando ou paradas, mesmo quando a
    pergunta chama isso de status. Não use para saber se a instância passou nas verificações
    de saúde: para isso, use verificar_status.

    Args:
        estado: Estado da instância. Sem estado, considera todas.
        regiao: Região AWS no formato us-east-1. Sem região, usa a região padrão da aplicação.
    """
    return consultar_instancias(estado, regiao)


@tool(parse_docstring=True)
def verificar_status(estado: Estado | None = None, regiao: str | None = None) -> str:
    """Verifica as checagens de saúde das instâncias EC2: status check de sistema e de instância.

    Use só quando a pergunta for sobre verificações de saúde, falha de hardware ou de rede da
    instância. Não use para saber se a instância está rodando ou parada, nem para listar
    instâncias: para isso, use listar_instancias.

    Args:
        estado: Estado da instância. Sem estado, considera todas.
        regiao: Região AWS no formato us-east-1. Sem região, usa a região padrão da aplicação.
    """
    return consultar_status(estado, regiao)
