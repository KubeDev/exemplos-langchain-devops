"""Busca por similaridade na coleção ativa ou numa coleção escolhida, sem enviar resultados a um LLM."""

import argparse
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVector

ROOT = Path(__file__).resolve().parents[2]
EMBEDDING_MODEL = "qwen3-embedding:0.6b"
# Tamanho do vetor que o modelo gera (está na documentação dele). O pgvector precisa
# desse número para criar a coluna vector(N); trocar de modelo exige reindexar.
EMBEDDING_DIMENSIONS = 1024

# O endereço do Ollama, a conexão do banco e a coleção ativa vêm do .env.
load_dotenv(ROOT / ".env")


def conferir_modelo(url: str, colecao: str) -> None:
    """Confere no banco o modelo que gerou os vetores persistidos."""
    try:
        with psycopg.connect(url) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("SELECT cmetadata FROM langchain_pg_collection WHERE name = %s", (colecao,))
                linha = cursor.fetchone()
    except psycopg.errors.UndefinedTable as exc:
        raise SystemExit(f"Coleção {colecao} ausente. Execute a indexação antes da busca.") from exc
    if linha is None:
        raise SystemExit(f"Coleção {colecao} ausente. Execute a indexação antes da busca.")
    esperado = {"model": EMBEDDING_MODEL, "dimensions": EMBEDDING_DIMENSIONS}
    if linha[0] != esperado:
        raise SystemExit(f"Embedding incompatível: índice={linha[0]}, consulta={esperado}. Reindexe {colecao}.")


def main() -> None:
    """Busca os k chunks mais próximos e imprime texto, origem e distância."""
    parser = argparse.ArgumentParser(description="Busca vetorial nos chunks indexados")
    parser.add_argument("pergunta")
    parser.add_argument("--k", type=int, default=3)
    # Sem --colecao, busca na coleção ativa; com ele, compara uma coleção nova antes da troca.
    parser.add_argument("--colecao", default=os.environ["COLECAO"])
    args = parser.parse_args()

    url = os.environ["DATABASE_URL"]
    conferir_modelo(url, args.colecao)
    banco = PGVector(
        embeddings=OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=os.environ["OLLAMA_URL"]),
        # O LangChain usa o driver psycopg: a URL precisa dizer isso.
        connection=url.replace("postgresql://", "postgresql+psycopg://", 1),
        collection_name=args.colecao,
        embedding_length=EMBEDDING_DIMENSIONS,
        use_jsonb=True,
    )
    resultados = banco.similarity_search_with_score(args.pergunta, k=args.k)

    caracteres = sum(len(documento.page_content) for documento, _ in resultados)
    print(f"Pergunta: {args.pergunta}")
    print(f"Coleção: {args.colecao} | k: {args.k} | {caracteres} caracteres recuperados")
    for posicao, (documento, distancia) in enumerate(resultados, start=1):
        origem = f"{documento.metadata['source']} ({documento.metadata['tipo']}, {documento.metadata['servico']})"
        print(f"\n{posicao}. Distância: {distancia:.4f} | Origem: {origem}")
        print(documento.page_content.strip())


if __name__ == "__main__":
    main()
