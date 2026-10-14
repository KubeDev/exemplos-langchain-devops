"""Divide a base com uma configuração, gera embeddings e reconstrói a coleção dela."""

import argparse
from collections import Counter

from langchain_postgres import PGVector

from .config import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL, colecao, database_url, embeddings, sqlalchemy_url
from .dividir import configuracao_a, configuracao_b


def main() -> None:
    """Indexa todos os dados com a configuração A ou B."""
    parser = argparse.ArgumentParser(description="Indexa a base com uma configuração de chunk")
    parser.add_argument("--config", choices=["a", "b"], required=True)
    args = parser.parse_args()

    chunks = configuracao_a() if args.config == "a" else configuracao_b()

    por_tipo = Counter(chunk.metadata["tipo"] for chunk in chunks)
    for tipo, quantidade in sorted(por_tipo.items()):
        print(f"{tipo:>12}: {quantidade} chunks")
    caracteres = sum(len(chunk.page_content) for chunk in chunks)
    print(f"Total: {len(chunks)} chunks | {caracteres} caracteres enviados ao modelo de embedding")

    print(f"Gerando embeddings com {EMBEDDING_MODEL} ({EMBEDDING_DIMENSIONS} dimensões)...")
    modelo = embeddings()
    vetores = modelo.embed_documents([chunk.page_content for chunk in chunks])

    banco = PGVector(
        embeddings=modelo,
        connection=sqlalchemy_url(database_url()),
        collection_name=colecao(args.config),
        collection_metadata={"model": EMBEDDING_MODEL, "dimensions": EMBEDDING_DIMENSIONS},
        embedding_length=EMBEDDING_DIMENSIONS,
        pre_delete_collection=True,
        use_jsonb=True,
    )
    banco.add_embeddings(
        texts=[chunk.page_content for chunk in chunks],
        embeddings=vetores,
        metadatas=[chunk.metadata for chunk in chunks],
        ids=[f"{args.config}-{numero}" for numero in range(len(chunks))],
    )
    print(f"Persistidos: {len(chunks)} chunks na coleção {colecao(args.config)}.")


if __name__ == "__main__":
    main()
