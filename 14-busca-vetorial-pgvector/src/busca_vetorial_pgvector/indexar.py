"""Extrai documentos, gera embeddings e reconstrói a coleção vetorial."""

from pathlib import Path

from langchain_core.documents import Document
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


def carregar_markdown(arquivo: Path) -> list[Document]:
    """Lê um runbook Markdown como uma unidade recuperável."""
    texto = arquivo.read_text(encoding="utf-8").strip()
    if not texto:
        raise SystemExit(f"O arquivo {arquivo.name} não contém texto extraível.")
    return [Document(id=arquivo.name, page_content=texto, metadata={"source": arquivo.name, "format": "md"})]


def carregar_pdf(arquivo: Path) -> list[Document]:
    """Extrai todo o PDF como uma única unidade recuperável."""
    textos = []
    for numero, pagina in enumerate(PdfReader(arquivo).pages, start=1):
        texto = (pagina.extract_text() or "").strip()
        if not texto:
            raise SystemExit(f"A página {numero} de {arquivo.name} não contém texto extraível.")
        textos.append(texto)
    if not textos:
        raise SystemExit(f"O PDF {arquivo.name} não contém páginas.")
    return [
        Document(
            id=arquivo.name,
            page_content="\n\n".join(textos),
            metadata={"source": arquivo.name, "format": "pdf", "pages": len(textos)},
        )
    ]


def main() -> None:
    """Lê PDF e Markdown e persiste seus textos com vetores no pgvector."""
    arquivos = sorted([*DATA_DIR.glob("*.md"), *DATA_DIR.glob("*.pdf")])
    if not arquivos:
        raise SystemExit(f"Nenhum PDF ou Markdown encontrado em {DATA_DIR}.")

    documentos: list[Document] = []
    for arquivo in arquivos:
        carregados = carregar_pdf(arquivo) if arquivo.suffix == ".pdf" else carregar_markdown(arquivo)
        documentos.extend(carregados)
        print(f"Extraído: {arquivo.name} ({len(carregados)} unidade(s))")

    print(f"Gerando {len(documentos)} embeddings com {EMBEDDING_MODEL} ({EMBEDDING_DIMENSIONS} dimensões)...")
    modelo = embeddings()
    vetores = modelo.embed_documents([documento.page_content for documento in documentos])
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
    banco.add_embeddings(
        texts=[documento.page_content for documento in documentos],
        embeddings=vetores,
        metadatas=[documento.metadata for documento in documentos],
        ids=[documento.id for documento in documentos],
    )
    print(f"Persistidos: {len(documentos)} documentos na coleção {COLLECTION}.")


if __name__ == "__main__":
    main()
