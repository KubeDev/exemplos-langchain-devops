"""Log narrativo — a interface da aula.

Numa apresentacao ao vivo o terminal e o que a turma ve, entao o log precisa
CONTAR o que esta acontecendo, nao apenas registrar eventos: um bloco por
etapa, legivel de longe.

Sao so helpers de formatacao em cima do `logging` da biblioteca padrao. Quem
chama e o fluxo em `chains.py`, linha a linha — assim o log acompanha o codigo
na mesma ordem em que ele e lido.
"""

import logging
import os
import sys

_LARGURA = 72
log = logging.getLogger("triagem")


def configurar() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    log.handlers = [handler]
    log.setLevel(logging.INFO)
    log.propagate = False
    # O httpx e barulhento e competiria com a narrativa em tela.
    logging.getLogger("httpx").setLevel(logging.WARNING)


def verbose() -> bool:
    return os.getenv("LOG_VERBOSE", "1") == "1"


def banner(titulo: str) -> None:
    texto = f"─── ▶ {titulo.upper()} "
    log.info("")
    log.info(texto + "─" * max(0, _LARGURA - len(texto)))


def caixa(texto: str) -> None:
    log.info("")
    log.info("╔" + "═" * _LARGURA + "╗")
    log.info("║" + f"  {texto}".ljust(_LARGURA) + "║")
    log.info("╚" + "═" * _LARGURA + "╝")


def campo(rotulo: str, valor: object) -> None:
    log.info(f"    {rotulo:<20} {valor}")


def bloco(rotulo: str, texto: str) -> None:
    """So aparece com LOG_VERBOSE=1 — e o que se corta para 'so mostrar'."""
    if not verbose():
        return
    log.info(f"    {rotulo}")
    for linha_texto in str(texto).splitlines():
        log.info(f"      │ {linha_texto}")


def resumo(rota: str, arquivos: list[str], segundos: float) -> None:
    log.info("")
    log.info("═" * _LARGURA)
    campo("rota", rota)
    campo("tempo total", f"{segundos:.1f}s")
    for caminho in arquivos:
        campo("ticket gravado", caminho)
    log.info("═" * _LARGURA)
    log.info("")
