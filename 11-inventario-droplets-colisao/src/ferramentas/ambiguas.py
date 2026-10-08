from langchain.tools import tool

from src.droplets import consultar_droplets
from src.saude import consultar_saude


@tool
def listar_droplets(regiao: str | None = None) -> str:
    """Consulta os Droplets da conta DigitalOcean.

    Args:
        regiao: Slug da região em minúsculas, como nyc1. Sem região, considera todos.
    """
    return consultar_droplets(regiao, None, None, None)


@tool
def verificar_saude(regiao: str | None = None) -> str:
    """Consulta a situação dos Droplets da conta DigitalOcean.

    Args:
        regiao: Slug da região em minúsculas, como nyc1. Sem região, considera todos.
    """
    return consultar_saude(regiao)
