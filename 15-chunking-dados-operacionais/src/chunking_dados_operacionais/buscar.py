"""Busca por similaridade numa coleção, sem enviar resultados a um LLM."""

import argparse

import psycopg
from langchain_postgres import PGVector

from .config import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL, colecao, database_url, embeddings, sqlalchemy_url


def conferir_modelo(url: str, nome: str) -> None:
    """Confere no banco o modelo que gerou os vetores persistidos."""
    try:
        with psycopg.connect(url) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("SELECT cmetadata FROM langchain_pg_collection WHERE name = %s", (nome,))
                linha = cursor.fetchone()
    except psycopg.errors.UndefinedTable as exc:
        raise SystemExit(f"Coleção {nome} ausente. Execute 'uv run indexar' antes da busca.") from exc
    if linha is None:
        raise SystemExit(f"Coleção {nome} ausente. Execute 'uv run indexar' antes da busca.")
    esperado = {"model": EMBEDDING_MODEL, "dimensions": EMBEDDING_DIMENSIONS}
    if linha[0] != esperado:
        raise SystemExit(f"Embedding incompatível: índice={linha[0]}, consulta={esperado}. Reindexe {nome}.")


def abrir_colecao(configuracao: str) -> PGVector:
    """Abre a coleção de uma configuração depois de conferir o modelo."""
    url = database_url()
    conferir_modelo(url, colecao(configuracao))
    return PGVector(
        embeddings=embeddings(),
        connection=sqlalchemy_url(url),
        collection_name=colecao(configuracao),
        embedding_length=EMBEDDING_DIMENSIONS,
        use_jsonb=True,
    )


def main() -> None:
    """Busca os k chunks mais próximos e imprime texto, origem e distância."""
    parser = argparse.ArgumentParser(description="Busca vetorial numa configuração de chunk")
    parser.add_argument("pergunta")
    parser.add_argument("--config", choices=["a", "b"], required=True)
    parser.add_argument("--k", type=int, default=3)
    args = parser.parse_args()

    resultados = abrir_colecao(args.config).similarity_search_with_score(args.pergunta, k=args.k)

    caracteres = sum(len(documento.page_content) for documento, _ in resultados)
    print(f"Pergunta: {args.pergunta}")
    print(f"Coleção: {colecao(args.config)} | k: {args.k} | {caracteres} caracteres recuperados")
    for posicao, (documento, distancia) in enumerate(resultados, start=1):
        origem = f"{documento.metadata['source']} ({documento.metadata['tipo']}, {documento.metadata.get('servico', '?')})"
        print(f"\n{posicao}. Distância: {distancia:.4f} | Origem: {origem}")
        print(documento.page_content.strip())


if __name__ == "__main__":
    main()
