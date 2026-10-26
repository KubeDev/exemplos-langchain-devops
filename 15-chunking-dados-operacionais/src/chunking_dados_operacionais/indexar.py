"""Divide a base pela natureza de cada dado, gera embeddings e reconstrói a coleção.

As estratégias de divisão vêm de gerar_chunks.py: o mesmo recursivo e a mesma seção da demo,
agora aplicados à base inteira.
"""

import os
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from pypdf import PdfReader

from chunking_dados_operacionais.gerar_chunks import (
    SOBREPOSICAO_LONGO,
    TAMANHO_LONGO,
    dividir_por_secao,
    dividir_recursivo,
)

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "dados"
COLECAO = "chunks"
EMBEDDING_MODEL = "text-embedding-3-small"
# Tamanho do vetor que o modelo gera (está na documentação dele). O pgvector precisa
# desse número para criar a coluna vector(N); trocar de modelo exige reindexar.
EMBEDDING_DIMENSIONS = 1536

# A chave da OpenAI e a conexão do banco vêm do .env.
load_dotenv(ROOT / ".env")

# ---------------------------------------------------------------------------
# Documentos: leitura do arquivo e metadado tirado do nome
# ---------------------------------------------------------------------------

# O nome do arquivo diz o tipo e o serviço: RB-381-payments-worker.md é um runbook do payments-worker.
TIPOS = {"RB": "runbook", "ARQ": "arquitetura", "REF": "referência", "PM": "post-mortem"}
SERVICOS = ["catalog-api", "payments-worker", "image-processor"]


def metadados(arquivo: Path) -> dict:
    """Monta o metadado do documento a partir do nome do arquivo."""
    tipo = TIPOS[arquivo.name.split("-")[0]]
    for servico in SERVICOS:
        if servico in arquivo.name:
            return {"source": arquivo.name, "tipo": tipo, "servico": servico}
    raise ValueError(f"Serviço desconhecido no nome do arquivo: {arquivo.name}")


def carregar_markdown(arquivo: Path) -> Document:
    """Lê o documento Markdown inteiro."""
    return Document(page_content=arquivo.read_text(encoding="utf-8"), metadata=metadados(arquivo))


def carregar_pdf(arquivo: Path) -> Document:
    """Extrai o texto de todas as páginas do post-mortem."""
    texto = "\n\n".join(pagina.extract_text() for pagina in PdfReader(arquivo).pages)
    return Document(page_content=texto, metadata=metadados(arquivo))


def main() -> None:
    """Divide a base pela natureza de cada dado e indexa os chunks numa coleção do pgvector."""
    # A base inteira: a estratégia segue a natureza de cada dado.
    chunks = []
    # Markdown tem títulos: cada seção vira um chunk.
    for arquivo in sorted(DATA_DIR.glob("*.md")):
        chunks += dividir_por_secao(carregar_markdown(arquivo))
    # O PDF perde os títulos na extração: recursivo. Linha do tempo e causa são resposta longa,
    # por isso o ponto de partida longo (2000/400); é hipótese, não medição.
    for arquivo in sorted(DATA_DIR.glob("*.pdf")):
        chunks += dividir_recursivo(carregar_pdf(arquivo), TAMANHO_LONGO, SOBREPOSICAO_LONGO)

    por_tipo = Counter(chunk.metadata["tipo"] for chunk in chunks)
    for tipo, quantidade in sorted(por_tipo.items()):
        # O maior chunk de cada tipo é a medição: ele precisa caber no limite do modelo de embedding.
        maior = max(len(chunk.page_content) for chunk in chunks if chunk.metadata["tipo"] == tipo)
        print(f"{tipo}: {quantidade} chunks | maior com {maior} caracteres")
    caracteres = sum(len(chunk.page_content) for chunk in chunks)
    print(f"Total: {len(chunks)} chunks | {caracteres} caracteres enviados ao modelo de embedding")

    print(f"Gerando embeddings com {EMBEDDING_MODEL} ({EMBEDDING_DIMENSIONS} dimensões)...")
    modelo = OpenAIEmbeddings(model=EMBEDDING_MODEL, dimensions=EMBEDDING_DIMENSIONS)
    vetores = modelo.embed_documents([chunk.page_content for chunk in chunks])

    banco = PGVector(
        embeddings=modelo,
        # O LangChain usa o driver psycopg: a URL precisa dizer isso.
        connection=os.environ["DATABASE_URL"].replace("postgresql://", "postgresql+psycopg://", 1),
        collection_name=COLECAO,
        collection_metadata={"model": EMBEDDING_MODEL, "dimensions": EMBEDDING_DIMENSIONS},
        embedding_length=EMBEDDING_DIMENSIONS,
        pre_delete_collection=True,
        use_jsonb=True,
    )
    banco.add_embeddings(
        texts=[chunk.page_content for chunk in chunks],
        embeddings=vetores,
        metadatas=[chunk.metadata for chunk in chunks],
        ids=[f"chunk-{numero}" for numero in range(len(chunks))],
    )
    print(f"Persistidos: {len(chunks)} chunks na coleção {COLECAO}.")


if __name__ == "__main__":
    main()
