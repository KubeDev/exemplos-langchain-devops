"""Mostra como um arquivo é dividido, sem gerar embedding nem gravar no banco."""

import argparse
import statistics
from pathlib import Path

from .dividir import (
    carregar_eventos,
    carregar_markdown,
    carregar_pdf,
    carregar_texto,
    carregar_tickets,
    dividir_por_secao,
    dividir_por_tamanho,
    dividir_tickets,
    janelas_de_log,
)

ESTRATEGIAS = ["inteiro", "tamanho", "secao", "janela", "ticket"]


def main() -> None:
    """Divide um arquivo com a estratégia escolhida e imprime os chunks."""
    parser = argparse.ArgumentParser(description="Visualiza os chunks de um arquivo")
    parser.add_argument("arquivo", type=Path)
    parser.add_argument("--estrategia", choices=ESTRATEGIAS, default="tamanho")
    parser.add_argument("--tamanho", type=int, default=1000, help="Caracteres por chunk (padrão: 1000)")
    parser.add_argument("--sobreposicao", type=int, default=0, help="Caracteres, ou segundos na janela de log")
    parser.add_argument("--segundos", type=int, default=60, help="Duração da janela de log (padrão: 60)")
    parser.add_argument("--contendo", help="Mostra só os chunks que contêm este texto")
    args = parser.parse_args()

    if args.arquivo.suffix == ".pdf":
        documento = carregar_pdf(args.arquivo)
    elif args.arquivo.suffix == ".md":
        documento = carregar_markdown(args.arquivo)
    else:
        documento = carregar_texto(args.arquivo)

    if args.estrategia == "inteiro":
        chunks = [documento]
    elif args.estrategia == "tamanho":
        chunks = dividir_por_tamanho(documento, args.tamanho, args.sobreposicao)
    elif args.estrategia == "secao":
        chunks = dividir_por_secao(documento, args.tamanho, args.sobreposicao)
    elif args.estrategia == "janela":
        chunks = janelas_de_log(carregar_eventos(args.arquivo), args.arquivo.name, args.segundos, args.sobreposicao)
    else:
        chunks = dividir_tickets(carregar_tickets(args.arquivo), args.arquivo.name, args.tamanho)

    for posicao, chunk in enumerate(chunks, start=1):
        if args.contendo and args.contendo.lower() not in chunk.page_content.lower():
            continue
        detalhes = [f"{len(chunk.page_content)} caracteres"]
        if "start_index" in chunk.metadata:
            detalhes.append(f"posição {chunk.metadata['start_index']}")
        if "secao" in chunk.metadata:
            detalhes.append(f"seção: {chunk.metadata['secao']}")
        if "inicio" in chunk.metadata:
            detalhes.append(f"janela {chunk.metadata['inicio'][11:19]} a {chunk.metadata['fim'][11:19]}")
        print(f"\n===== chunk {posicao}/{len(chunks)} | " + " | ".join(detalhes))
        print(chunk.page_content)

    tamanhos = [len(chunk.page_content) for chunk in chunks]
    print(f"\n{args.arquivo.name} | estratégia: {args.estrategia} | {len(chunks)} chunks | {sum(tamanhos)} caracteres")
    print(f"Tamanho dos chunks: mínimo {min(tamanhos)} | mediana {int(statistics.median(tamanhos))} | máximo {max(tamanhos)}")


if __name__ == "__main__":
    main()
