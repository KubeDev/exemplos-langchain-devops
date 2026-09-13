"""O contrato da API: o unico Pydantic do projeto, e ele fica na fronteira.

Nada aqui participa das chains — daqui para dentro tudo e texto.
Por que so na borda: README, "Onde o schema entra (e onde nao entra)".
"""

from typing import Any

from pydantic import BaseModel, Field


class Alerta(BaseModel):
    """O que chega no webhook."""

    titulo: str
    servico: str
    severidade: str = "nao informada"
    logs: list[str] = Field(default_factory=list)
    metricas: dict[str, Any] = Field(default_factory=dict)

    def como_texto(self) -> str:
        """Converte o alerta em texto para o prompt — e aqui que o objeto vira
        string. Dessa linha em diante o exemplo so lida com texto."""
        linhas = [
            f"Titulo: {self.titulo}",
            f"Servico: {self.servico}",
            f"Severidade na origem: {self.severidade}",
        ]
        if self.metricas:
            metricas = ", ".join(f"{k}={v}" for k, v in self.metricas.items())
            linhas.append(f"Metricas: {metricas}")
        if self.logs:
            linhas.append("Logs:")
            linhas.extend(f"  [{i}] {linha}" for i, linha in enumerate(self.logs))
        else:
            linhas.append("Logs: (nenhum log acompanha este alerta)")
        return "\n".join(linhas)
