"""Busca conteúdo por similaridade, sem enviar resultados a um LLM."""

import argparse

import psycopg
from langchain_postgres import PGVector

from .config import (
    COLLECTION,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    database_url,
    embeddings,
    sqlalchemy_url,
)


def quantidade_positiva(valor: str) -> int:
    """Converte o argumento --k e rejeita valores sem resultado possível."""
    try:
        quantidade = int(valor)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--k precisa ser um número inteiro.") from exc
    if quantidade < 1:
        raise argparse.ArgumentTypeError("--k precisa ser maior que zero.")
    return quantidade


def conferir_modelo(url: str) -> None:
    """Confere no banco o modelo que gerou os vetores persistidos."""
    try:
        with psycopg.connect(url) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    "SELECT cmetadata FROM langchain_pg_collection WHERE name = %s",
                    (COLLECTION,),
                )
                linha = cursor.fetchone()
    except psycopg.errors.UndefinedTable as exc:
        raise SystemExit("Coleção ausente. Execute 'uv run indexar' antes da busca.") from exc
    if linha is None:
        raise SystemExit("Coleção ausente. Execute 'uv run indexar' antes da busca.")
    esperado = {"model": EMBEDDING_MODEL, "dimensions": EMBEDDING_DIMENSIONS}
    if linha[0] != esperado:
        raise SystemExit(
            f"Embedding incompatível: índice={linha[0]}, consulta={esperado}. "
            "Reconstrua o índice com 'uv run indexar'."
        )


def main() -> None:
    """Busca os k documentos mais próximos e imprime texto e origem."""
    parser = argparse.ArgumentParser(description="Busca vetorial nos documentos operacionais")
    parser.add_argument("pergunta", help="Pergunta formulada em linguagem natural")
    parser.add_argument("--k", type=quantidade_positiva, default=3, help="Máximo de resultados (padrão: 3)")
    args = parser.parse_args()

    url = database_url()
    conferir_modelo(url)
    banco = PGVector(
        embeddings=embeddings(),
        connection=sqlalchemy_url(url),
        collection_name=COLLECTION,
        embedding_length=EMBEDDING_DIMENSIONS,
        use_jsonb=True,
    )
    resultados = banco.similarity_search_with_score(args.pergunta, k=args.k)

    print(f"Pergunta: {args.pergunta}")
    print(f"Modelo: {EMBEDDING_MODEL} | k: {args.k} | métrica: distância de cosseno (menor = mais próximo)")
    caracteres = sum(len(documento.page_content) for documento, _ in resultados)
    print(f"Recuperados: {len(resultados)} unidades | {caracteres} caracteres de texto")
    if not resultados:
        print("Nenhum documento encontrado.")
    for posicao, (documento, distancia) in enumerate(resultados, start=1):
        origem = documento.metadata["source"]
        pagina = documento.metadata.get("page")
        paginas = documento.metadata.get("pages")
        local = origem
        if pagina:
            local = f"{origem}, página {pagina}"
        elif paginas:
            local = f"{origem}, PDF inteiro ({paginas} páginas)"
        print(f"\n{posicao}. Distância: {distancia:.4f} | Origem: {local}")
        print(documento.page_content.strip())


if __name__ == "__main__":
    main()
