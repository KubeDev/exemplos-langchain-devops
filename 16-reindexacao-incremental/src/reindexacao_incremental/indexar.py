"""Indexação incremental: recebe um documento e só reprocessa se o conteúdo mudou.

Compara o arquivo com o que está na coleção ativa. O nome do arquivo é o identificador do
documento: dados/v2/RB-274-catalog-api.md atualiza o RB-274 que veio da v1. A carga inicial,
a base inteira de uma pasta, é do reindexar.

A divisão em chunks é a mesma de reindexar.py, copiada de propósito: cada arquivo se lê
sozinho, sem navegar entre arquivos. Ao mudar a divisão, mude nos dois lugares.
"""

import argparse
import hashlib
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import MarkdownHeaderTextSplitter

ROOT = Path(__file__).resolve().parents[2]
EMBEDDING_MODEL = "qwen3-embedding:0.6b"
# Tamanho do vetor que o modelo gera (está na documentação dele). O pgvector precisa
# desse número para criar a coluna vector(N); trocar de modelo exige reindexar.
EMBEDDING_DIMENSIONS = 1024

# O endereço do Ollama, a conexão do banco e a coleção ativa vêm do .env.
load_dotenv(ROOT / ".env")
COLECAO = os.environ["COLECAO"]

# ---------------------------------------------------------------------------
# Documentos: um chunk por seção do Markdown
# ---------------------------------------------------------------------------

# O nome do arquivo diz o tipo e o serviço: RB-381-payments-worker.md é um runbook do payments-worker.
TIPOS = {"RB": "runbook", "ARQ": "arquitetura"}
SERVICOS = ["catalog-api", "payments-worker", "image-processor"]


def metadados(arquivo: Path) -> dict:
    """Monta o metadado do documento a partir do nome do arquivo."""
    tipo = TIPOS[arquivo.name.split("-")[0]]
    for servico in SERVICOS:
        if servico in arquivo.name:
            return {"source": arquivo.name, "tipo": tipo, "servico": servico}
    raise ValueError(f"Serviço desconhecido no nome do arquivo: {arquivo.name}")


def dividir(arquivo: Path) -> list[Document]:
    """Corta nos títulos Markdown e põe o título no texto do chunk."""
    documento = metadados(arquivo)
    titulos = [("#", "h1"), ("##", "h2")]
    secoes = MarkdownHeaderTextSplitter(headers_to_split_on=titulos).split_text(
        arquivo.read_text(encoding="utf-8")
    )

    chunks = []
    for secao in secoes:
        caminho = " > ".join(secao.metadata.values())
        texto = f"[{documento['servico']} | {documento['tipo']}] {caminho}\n\n{secao.page_content}"
        chunks.append(Document(page_content=texto, metadata={**documento, "secao": caminho}))
    return chunks


# ---------------------------------------------------------------------------
# O que mudou: o arquivo comparado com o índice
# ---------------------------------------------------------------------------


def hash_do_arquivo(arquivo: Path) -> str:
    """Impressão digital do conteúdo: muda se um byte do arquivo mudar."""
    return hashlib.sha256(arquivo.read_bytes()).hexdigest()


def estado_no_indice(url: str, source: str) -> dict | None:
    """Lê do banco o hash gravado e os IDs dos chunks do documento, ou None se ele não está lá."""
    try:
        with psycopg.connect(url) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT e.id, e.cmetadata->>'hash'
                    FROM langchain_pg_embedding e
                    JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                    WHERE c.name = %s AND e.cmetadata->>'source' = %s
                    """,
                    (COLECAO, source),
                )
                linhas = cursor.fetchall()
    except psycopg.errors.UndefinedTable:
        # Banco vazio: as tabelas nascem na primeira gravação.
        return None

    if not linhas:
        return None
    # Todos os chunks do documento levam o mesmo hash: basta o da primeira linha.
    return {"hash": linhas[0][1], "ids": [id_chunk for id_chunk, _ in linhas]}


def main() -> None:
    """Compara o documento com a coleção ativa e grava só se ele mudou."""
    parser = argparse.ArgumentParser(description="Indexação incremental de um documento")
    parser.add_argument("arquivo", help="o arquivo .md do documento, como dados/v2/RB-274-catalog-api.md")
    args = parser.parse_args()

    arquivo = Path(args.arquivo)
    if not arquivo.is_file():
        raise SystemExit(f"{arquivo} não é um arquivo. Passe um .md, como dados/v2/RB-274-catalog-api.md.")

    url = os.environ["DATABASE_URL"]
    hash_atual = hash_do_arquivo(arquivo)
    anterior = estado_no_indice(url, arquivo.name)

    # Mesmo hash: o conteúdo é o mesmo, nada a fazer e nenhuma chamada ao modelo.
    if anterior and anterior["hash"] == hash_atual:
        print(f"igual: {arquivo.name} | coleção {COLECAO}")
        return

    modelo = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=os.environ["OLLAMA_URL"])
    chunks = dividir(arquivo)
    vetores = modelo.embed_documents([chunk.page_content for chunk in chunks])

    banco = PGVector(
        embeddings=modelo,
        # O LangChain usa o driver psycopg: a URL precisa dizer isso.
        connection=url.replace("postgresql://", "postgresql+psycopg://", 1),
        collection_name=COLECAO,
        collection_metadata={"model": EMBEDDING_MODEL, "dimensions": EMBEDDING_DIMENSIONS},
        embedding_length=EMBEDDING_DIMENSIONS,
        use_jsonb=True,
    )

    if anterior:
        # Alterado: saem todos os chunks antigos do documento, entram os novos.
        banco.delete(ids=anterior["ids"], collection_only=True)
        situacao = "alterado"
    else:
        situacao = "novo"
    banco.add_embeddings(
        texts=[chunk.page_content for chunk in chunks],
        embeddings=vetores,
        # O hash vai junto: é ele que a próxima execução compara.
        metadatas=[{**chunk.metadata, "hash": hash_atual} for chunk in chunks],
        # ID estável: coleção, documento e posição do chunk no documento.
        ids=[f"{COLECAO}/{arquivo.name}#{numero}" for numero in range(len(chunks))],
    )
    print(f"{situacao}: {arquivo.name} | {len(chunks)} chunks | coleção {COLECAO}")


if __name__ == "__main__":
    main()
