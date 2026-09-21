"""Formatacao do log de execucao do agente.

Este log nao e observabilidade: e a interface da aula. E aqui que o aluno ve o
agente escolher uma ferramenta, chamar, receber o resultado e decidir o proximo
passo. Mudanca que reduza a legibilidade na tela e regressao, nao limpeza.

A formatacao mora neste arquivo para nao competir com a licao em `app.py` --
la ficam apenas as chamadas, na ordem em que o codigo e lido.

Duas decisoes aqui existem por causa da tela, e nao devem ser "simplificadas":

1. Caminhos aparecem relativos a raiz do projeto analisado. O agente trabalha
   com caminhos absolutos, que ocupam tres linhas no projetor e escondem a
   informacao que importa (qual arquivo ele abriu).
2. O retorno repete o numero da chamada. O modelo chama varias ferramentas em
   paralelo, entao os retornos chegam fora de ordem -- sem o numero, nao da
   para saber qual resposta e de qual chamada.
"""

from rich.console import Console

console = Console()

# Previa do retorno de cada ferramenta. Truncar e obrigatorio: um `read_file`
# de arquivo inteiro rola a tela e faz a demonstracao perder o fio.
LARGURA_PREVIA = 76

_raiz = ""


def definir_raiz(caminho: str) -> None:
    """Caminhos do log passam a ser exibidos relativos a este diretorio."""
    global _raiz
    _raiz = caminho.rstrip("/")


def _encurtar(valor):
    """Troca o caminho absoluto do projeto por um caminho relativo."""
    if not isinstance(valor, str) or not _raiz:
        return valor
    if valor == _raiz:
        return "."
    if valor.startswith(_raiz + "/"):
        return valor[len(_raiz) + 1:]
    return valor


def _formatar_argumentos(argumentos: dict) -> str:
    """Transforma {"dir_path": "/longo/caminho/src"} em 'dir_path="src"'."""
    return ", ".join(
        f"{chave}={_encurtar(valor)!r}" for chave, valor in argumentos.items()
    )


def _formatar_tamanho(conteudo: str) -> str:
    if len(conteudo) < 1024:
        return f"{len(conteudo)} chars"
    return f"{len(conteudo) / 1024:.1f} KB"


def log_chamada(passo: int, ferramenta: str, argumentos: dict) -> None:
    """O agente decidiu chamar uma ferramenta."""
    console.print(
        f"\n[bold cyan]\\[{passo}][/bold cyan] "
        f"[bold]{ferramenta}[/bold]"
        f"([dim]{_formatar_argumentos(argumentos)}[/dim])",
        highlight=False,
    )


def log_retorno(passo: int, conteudo: str) -> None:
    """O que a ferramenta devolveu, em uma linha."""
    etiqueta = f"    [cyan]\\[{passo}][/cyan] [green]->[/green]"

    # As ferramentas ecoam o caminho absoluto nas mensagens de erro.
    if _raiz:
        conteudo = conteudo.replace(_raiz, ".")

    if conteudo.startswith("Error:") or conteudo.startswith("No files found"):
        primeira = conteudo.splitlines()[0]
        console.print(f"{etiqueta} [yellow]{primeira[:LARGURA_PREVIA]}[/yellow]",
                      highlight=False)
        return

    linhas = [linha.strip() for linha in conteudo.splitlines() if linha.strip()]

    if not linhas:
        console.print(f"{etiqueta} [dim]nenhum resultado[/dim]", highlight=False)
        return

    previa = ", ".join(linhas)
    if len(previa) > LARGURA_PREVIA:
        previa = previa[:LARGURA_PREVIA] + "..."

    console.print(
        f"{etiqueta} {previa} [dim]({_formatar_tamanho(conteudo)})[/dim]",
        highlight=False,
    )
