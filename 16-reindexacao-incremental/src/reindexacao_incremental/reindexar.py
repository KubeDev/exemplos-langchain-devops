"""Reindexação total: gera de novo, sem olhar o hash, a base inteira na coleção apontada pela COLECAO.

Serve para a mudança que não está nos arquivos, como a troca do modelo de embedding: o hash
continua igual e o indexar não reprocessaria nada.

- COLECAO de uma coleção que já existe: apaga a coleção e cria de novo, com a base inteira da pasta.
- COLECAO de uma coleção nova: cria a coleção ao lado da anterior, que continua intacta. Para gerar
  sem trocar a ativa, passe a variável só para o comando: COLECAO=base_v2 uv run reindexar dados/v2.
  A troca é a COLECAO no .env, e o rollback é voltar a linha.

A divisão em chunks é a mesma de indexar.py, copiada de propósito: cada arquivo se lê
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

# O endereço do Ollama, a conexão do banco e a coleção que recebe a reindexação vêm do .env.
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


def hash_do_arquivo(arquivo: Path) -> str:
    """Impressão digital do conteúdo: a mesma que o indexar compara."""
    return hashlib.sha256(arquivo.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# A coleção de destino
# ---------------------------------------------------------------------------


def colecao_existe(url: str) -> bool:
    """Confere no banco se a coleção da COLECAO já foi criada."""
    try:
        with psycopg.connect(url) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("SELECT 1 FROM langchain_pg_collection WHERE name = %s", (COLECAO,))
                return cursor.fetchone() is not None
    except psycopg.errors.UndefinedTable:
        return False


def main() -> None:
    """Gera de novo a base inteira da pasta, com ou sem mudança nos arquivos."""
    parser = argparse.ArgumentParser(description="Reindexação total na coleção da COLECAO")
    parser.add_argument("pasta", help="a pasta da versão, como dados/v1")
    args = parser.parse_args()

    pasta = Path(args.pasta)
    if not pasta.is_dir():
        raise SystemExit(f"{pasta} não é uma pasta. Passe a pasta da versão, como dados/v1.")

    url = os.environ["DATABASE_URL"]
    existe = colecao_existe(url)

    # Os embeddings vêm antes de apagar: se o modelo falhar, a coleção continua como estava.
    modelo = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=os.environ["OLLAMA_URL"])
    arquivos = sorted(pasta.glob("*.md"))
    chunks = []
    ids = []
    for arquivo in arquivos:
        hash_atual = hash_do_arquivo(arquivo)
        do_arquivo = dividir(arquivo)
        # Mesmo ID e mesmo hash do indexar: depois da reindexação, o incremental continua de onde parou.
        for numero, chunk in enumerate(do_arquivo):
            chunk.metadata = {**chunk.metadata, "hash": hash_atual}
            ids.append(f"{COLECAO}/{arquivo.name}#{numero}")
        chunks += do_arquivo
        print(f"reindexado: {arquivo.name} | {len(do_arquivo)} chunks")
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

    if existe:
        # Apagar a coleção leva todos os chunks dela, até de documento que saiu da pasta.
        # Criada de novo, ela registra o modelo atual no cmetadata.
        banco.delete_collection()
        banco.create_collection()

    banco.add_embeddings(
        texts=[chunk.page_content for chunk in chunks],
        embeddings=vetores,
        metadatas=[chunk.metadata for chunk in chunks],
        ids=ids,
    )
    situacao = "existente, apagada e criada de novo" if existe else "nova, ao lado das outras"
    print(f"Coleção {COLECAO} ({situacao}) | documentos {len(arquivos)} | {len(chunks)} chunks gravados")


if __name__ == "__main__":
    main()
