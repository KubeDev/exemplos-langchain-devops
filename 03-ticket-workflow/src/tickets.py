"""Gravacao dos tickets em markdown.

Python puro, de proposito FORA das chains. A chain produz o relatorio; o que
se faz com ele — gravar em disco, abrir um Jira, mandar no Slack — e decisao
de quem chamou. O relatorio ja chega em markdown, escrito pelo modelo; aqui so
se acrescenta um cabecalho e o alerta original.

Note que `gravar` nao sabe se veio um relatorio ou dois: recebe o dicionario
que `triar()` montou e itera.
"""

import re
from datetime import datetime, timezone
from pathlib import Path

from src.schemas import Alerta

RAIZ = Path(__file__).resolve().parent.parent / "tickets"


def _slug(texto: str) -> str:
    limpo = re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")
    return limpo[:48] or "alerta"


def _montar(equipe: str, alerta: Alerta, categoria: str, relatorio: str) -> str:
    return "\n".join(
        [
            f"# {alerta.titulo}",
            "",
            f"> Ticket gerado automaticamente pela triagem · equipe **{equipe}**",
            f"> Servico: `{alerta.servico}` · severidade na origem: `{alerta.severidade}`",
            f"> Categoria da triagem: `{categoria}`",
            "",
            relatorio.strip(),
            "",
            "## Alerta recebido",
            "",
            "```",
            alerta.como_texto(),
            "```",
            "",
        ]
    )


def gravar(alerta: Alerta, categoria: str, relatorios: dict[str, str]) -> list[str]:
    """Um arquivo por relatorio. Devolve os caminhos gravados."""
    carimbo = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    caminhos: list[str] = []

    for equipe, relatorio in relatorios.items():
        destino = RAIZ / equipe
        destino.mkdir(parents=True, exist_ok=True)
        arquivo = destino / f"{carimbo}-{_slug(alerta.titulo)}.md"
        arquivo.write_text(_montar(equipe, alerta, categoria, relatorio), encoding="utf-8")
        caminhos.append(str(arquivo.relative_to(RAIZ.parent)))

    return caminhos
