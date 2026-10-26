"""Busca por similaridade nos chunks indexados, sem enviar resultados a um LLM."""

import argparse
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

ROOT = Path(__file__).resolve().parents[2]
COLECAO = "chunks"
EMBEDDING_MODEL = "text-embedding-3-small"
# Tamanho do vetor que o modelo gera (está na documentação dele). O pgvector precisa
# desse número para criar a coluna vector(N); trocar de modelo exige reindexar.
EMBEDDING_DIMENSIONS = 1536

# A chave da OpenAI e a conexão do banco vêm do .env.
load_dotenv(ROOT / ".env")


def conferir_modelo(url: str) -> None:
    """Confere no banco o modelo que gerou os vetores persistidos."""
    try:
        with psycopg.connect(url) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("SELECT cmetadata FROM langchain_pg_collection WHERE name = %s", (COLECAO,))
                linha = cursor.fetchone()
    except psycopg.errors.UndefinedTable as exc:
        raise SystemExit("Coleção ausente. Execute 'uv run indexar' antes da busca.") from exc
    if linha is None:
        raise SystemExit("Coleção ausente. Execute 'uv run indexar' antes da busca.")
    esperado = {"model": EMBEDDING_MODEL, "dimensions": EMBEDDING_DIMENSIONS}
    if linha[0] != esperado:
        raise SystemExit(f"Embedding incompatível: índice={linha[0]}, consulta={esperado}. Reindexe.")


def main() -> None:
    """Busca os k chunks mais próximos e imprime texto, origem e distância."""
    parser = argparse.ArgumentParser(description="Busca vetorial nos chunks indexados")
    parser.add_argument("pergunta")
    parser.add_argument("--k", type=int, default=3)
    args = parser.parse_args()

    url = os.environ["DATABASE_URL"]
    conferir_modelo(url)
    banco = PGVector(
        embeddings=OpenAIEmbeddings(model=EMBEDDING_MODEL, dimensions=EMBEDDING_DIMENSIONS),
        # O LangChain usa o driver psycopg: a URL precisa dizer isso.
        connection=url.replace("postgresql://", "postgresql+psycopg://", 1),
        collection_name=COLECAO,
        embedding_length=EMBEDDING_DIMENSIONS,
        use_jsonb=True,
    )
    resultados = banco.similarity_search_with_score(args.pergunta, k=args.k)

    caracteres = sum(len(documento.page_content) for documento, _ in resultados)
    print(f"Pergunta: {args.pergunta}")
    print(f"k: {args.k} | {caracteres} caracteres recuperados")
    for posicao, (documento, distancia) in enumerate(resultados, start=1):
        origem = f"{documento.metadata['source']} ({documento.metadata['tipo']}, {documento.metadata['servico']})"
        print(f"\n{posicao}. Distância: {distancia:.4f} | Origem: {origem}")
        print(documento.page_content.strip())


if __name__ == "__main__":
    main()
