"""Extrai documentos, gera embeddings e reconstrói a coleção vetorial."""

from langchain_postgres import PGVector
from pypdf import PdfReader

from .config import (
    COLLECTION,
    DATA_DIR,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    database_url,
    embeddings,
    sqlalchemy_url,
)


def main() -> None:
    """Lê PDF e Markdown e persiste seus textos com vetores no pgvector."""
    arquivos = sorted([*DATA_DIR.glob("*.md"), *DATA_DIR.glob("*.pdf")])
    if not arquivos:
        raise SystemExit(f"Nenhum PDF ou Markdown encontrado em {DATA_DIR}.")

    textos: list[str] = []
    metadados: list[dict] = []
    ids: list[str] = []

    for arquivo in arquivos:
        paginas = (
            [pagina.extract_text() for pagina in PdfReader(arquivo).pages]
            if arquivo.suffix == ".pdf"
            else [arquivo.read_text(encoding="utf-8")]
        )
        for numero, conteudo in enumerate(paginas, start=1):
            texto = (conteudo or "").strip()
            if not texto:
                raise SystemExit(f"O arquivo {arquivo.name} não contém texto extraível.")
            metadado = {"source": arquivo.name, "format": arquivo.suffix[1:]}
            if arquivo.suffix == ".pdf":
                metadado["page"] = numero
            textos.append(texto)
            metadados.append(metadado)
            ids.append(f"{arquivo.name}#p{numero}" if arquivo.suffix == ".pdf" else arquivo.name)
        print(f"Extraído: {arquivo.name} ({len(paginas)} unidade(s))")

    print(f"Gerando {len(textos)} embeddings com {EMBEDDING_MODEL} ({EMBEDDING_DIMENSIONS} dimensões)...")
    modelo = embeddings()
    vetores = modelo.embed_documents(textos)
    if any(len(vetor) != EMBEDDING_DIMENSIONS for vetor in vetores):
        raise SystemExit("O modelo retornou vetores com dimensão diferente da configurada.")

    banco = PGVector(
        embeddings=modelo,
        connection=sqlalchemy_url(database_url()),
        collection_name=COLLECTION,
        collection_metadata={"model": EMBEDDING_MODEL, "dimensions": EMBEDDING_DIMENSIONS},
        embedding_length=EMBEDDING_DIMENSIONS,
        pre_delete_collection=True,
        use_jsonb=True,
    )
    banco.add_embeddings(texts=textos, embeddings=vetores, metadatas=metadados, ids=ids)
    print(f"Persistidos: {len(ids)} documentos na coleção {COLLECTION}.")


if __name__ == "__main__":
    main()
