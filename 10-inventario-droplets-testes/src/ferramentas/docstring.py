from langchain.tools import tool

from src.droplets import consultar_droplets


@tool
def listar_droplets(
    regiao: str | None = None,
    status: str | None = None,
    memoria_minima_mb: int | None = None,
    memoria_maxima_mb: int | None = None,
) -> str:
    """Lista os Droplets da conta DigitalOcean, com filtros opcionais.

    Args:
        regiao: Slug da região em minúsculas, como nyc1. Sem região, lista todas.
        status: Status do Droplet: new, active, off ou archive. Sem status, lista todos.
        memoria_minima_mb: Memória mínima em MB, no mínimo 512.
        memoria_maxima_mb: Memória máxima em MB, no mínimo 512 e maior ou igual à mínima.
    """
    return consultar_droplets(regiao, status, memoria_minima_mb, memoria_maxima_mb)
