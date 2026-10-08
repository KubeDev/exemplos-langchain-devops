from typing import Literal

from langchain.tools import tool
from pydantic import BaseModel, Field, model_validator

from src.droplets import consultar_droplets


class FiltroDroplets(BaseModel):
    regiao: str | None = Field(
        default=None,
        pattern=r"^[a-z]{3}[0-9]$",
        description="Região do Droplet. Sem região, lista todas.",
    )
    status: Literal["new", "active", "off", "archive"] | None = Field(
        default=None, description="Status do Droplet. Sem status, lista todos."
    )
    memoria_minima_mb: int | None = Field(
        default=None, ge=512, description="Memória mínima do Droplet, em MB."
    )
    memoria_maxima_mb: int | None = Field(
        default=None, ge=512, description="Memória máxima do Droplet, em MB."
    )

    # Regra entre campos: não aparece no esquema enviado ao modelo, só vale na validação.
    @model_validator(mode="after")
    def minima_ate_maxima(self):
        if (
            self.memoria_minima_mb is not None
            and self.memoria_maxima_mb is not None
            and self.memoria_minima_mb > self.memoria_maxima_mb
        ):
            raise ValueError("memoria_minima_mb não pode ser maior que memoria_maxima_mb")
        return self


@tool(args_schema=FiltroDroplets)
def listar_droplets(
    regiao: str | None = None,
    status: str | None = None,
    memoria_minima_mb: int | None = None,
    memoria_maxima_mb: int | None = None,
) -> str:
    """Lista os Droplets da conta DigitalOcean, com filtros opcionais."""
    return consultar_droplets(regiao, status, memoria_minima_mb, memoria_maxima_mb)
