"""Compara as duas configurações com um conjunto de perguntas de fragmento esperado."""

import json

from .buscar import abrir_colecao
from .config import PERGUNTAS
from .dividir import configuracao_a, configuracao_b

K = 4


def normalizar(texto: str) -> str:
    """Ignora quebras de linha e espaços extras, comuns no texto extraído de PDF."""
    return " ".join(texto.split()).lower()


def completo(fragmentos: list[str], chunks: list) -> bool:
    """Verdadeiro se algum chunk contém todos os fragmentos esperados juntos."""
    return any(all(normalizar(f) in normalizar(chunk.page_content) for f in fragmentos) for chunk in chunks)


def main() -> None:
    """Mede duas coisas: se o chunking manteve a resposta inteira e se a busca a devolveu no top-k."""
    perguntas = json.loads(PERGUNTAS.read_text(encoding="utf-8"))
    indice = {"a": configuracao_a(), "b": configuracao_b()}
    colecoes = {"a": abrir_colecao("a"), "b": abrir_colecao("b")}
    totais = {c: {"indice": 0, "top": 0, "caracteres": 0} for c in colecoes}

    print(f"{'#':<3} {'Dado':<12} {'A: índice / top-' + str(K):<26} {'B: índice / top-' + str(K):<26}")
    for numero, item in enumerate(perguntas, start=1):
        linha = f"{numero:<3} {item['dado']:<12}"
        for configuracao, banco in colecoes.items():
            # 1. O chunking: a resposta existe inteira em algum chunk da coleção?
            no_indice = completo(item["fragmentos"], indice[configuracao])
            # 2. A busca: esse chunk voltou entre os k mais próximos da pergunta?
            resultados = banco.similarity_search(item["pergunta"], k=K)
            no_top = completo(item["fragmentos"], resultados)
            caracteres = sum(len(chunk.page_content) for chunk in resultados)

            totais[configuracao]["indice"] += no_indice
            totais[configuracao]["top"] += no_top
            totais[configuracao]["caracteres"] += caracteres
            marca = f"{'sim' if no_indice else 'não':<4}/ {'sim' if no_top else 'não':<4}{caracteres:>7} car."
            linha += f" {marca:<26}"
        print(linha)

    print(f"\n{len(perguntas)} perguntas | índice = resposta inteira em um chunk | top-{K} = chunk completo recuperado")
    for configuracao, total in totais.items():
        print(
            f"Configuração {configuracao.upper()}: índice {total['indice']}/{len(perguntas)} | "
            f"top-{K} {total['top']}/{len(perguntas)} | {total['caracteres']} caracteres recuperados"
        )


if __name__ == "__main__":
    main()
