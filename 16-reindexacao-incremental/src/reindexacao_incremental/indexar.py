"""Indexação incremental: reprocessa só o documento que mudou e remove o que saiu da pasta.

Com uma pasta, como dados/v1, compara a fonte inteira com a coleção ativa e remove o que saiu
dela. Com arquivos, compara só esses documentos e não remove nada. O nome do arquivo é o
identificador do documento: dados/v2/RB-274-catalog-api.md atualiza o RB-274 que veio da v1.

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
# O que mudou: a pasta comparada com o índice
# ---------------------------------------------------------------------------


def hash_do_arquivo(arquivo: Path) -> str:
    """Impressão digital do conteúdo: muda se um byte do arquivo mudar."""
    return hashlib.sha256(arquivo.read_bytes()).hexdigest()


def estado_no_indice(url: str) -> dict[str, dict]:
    """Lê do banco, por documento, o hash gravado e os IDs dos seus chunks."""
    try:
        with psycopg.connect(url) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT e.id, e.cmetadata->>'source', e.cmetadata->>'hash'
                    FROM langchain_pg_embedding e
                    JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                    WHERE c.name = %s
                    """,
                    (COLECAO,),
                )
                linhas = cursor.fetchall()
    except psycopg.errors.UndefinedTable:
        # Banco vazio: as tabelas nascem na primeira gravação.
        return {}

    documentos = {}
    for id_chunk, source, hash_gravado in linhas:
        documento = documentos.setdefault(source, {"hash": hash_gravado, "ids": []})
        documento["ids"].append(id_chunk)
    return documentos


def selecionar(caminhos: list[str]) -> tuple[list[Path], bool]:
    """Uma pasta é a fonte inteira; arquivos soltos são só esses documentos."""
    if len(caminhos) == 1 and Path(caminhos[0]).is_dir():
        return sorted(Path(caminhos[0]).glob("*.md")), True
    arquivos = [Path(caminho) for caminho in caminhos]
    for arquivo in arquivos:
        if not arquivo.is_file():
            raise SystemExit(f"{arquivo} não é um arquivo. Passe uma pasta só, como dados/v1, ou arquivos .md.")
    return arquivos, False


def main() -> None:
    """Compara os documentos com a coleção ativa e grava só a diferença."""
    parser = argparse.ArgumentParser(description="Indexação incremental de uma versão da base")
    parser.add_argument("caminhos", nargs="+", help="uma pasta, como dados/v1, ou arquivos .md")
    args = parser.parse_args()

    url = os.environ["DATABASE_URL"]
    modelo = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=os.environ["OLLAMA_URL"])
    banco = PGVector(
        embeddings=modelo,
        # O LangChain usa o driver psycopg: a URL precisa dizer isso.
        connection=url.replace("postgresql://", "postgresql+psycopg://", 1),
        collection_name=COLECAO,
        collection_metadata={"model": EMBEDDING_MODEL, "dimensions": EMBEDDING_DIMENSIONS},
        embedding_length=EMBEDDING_DIMENSIONS,
        use_jsonb=True,
    )

    selecionados, pasta_inteira = selecionar(args.caminhos)

    no_indice = estado_no_indice(url)
    novos = alterados = iguais = removidos = gravados = 0

    for arquivo in selecionados:
        hash_atual = hash_do_arquivo(arquivo)
        anterior = no_indice.get(arquivo.name)
        # Mesmo hash: o conteúdo é o mesmo, nada a fazer e nenhuma chamada ao modelo.
        if anterior and anterior["hash"] == hash_atual:
            iguais += 1
            continue

        chunks = dividir(arquivo)
        vetores = modelo.embed_documents([chunk.page_content for chunk in chunks])
        if anterior:
            # Alterado: saem todos os chunks antigos do documento, entram os novos.
            banco.delete(ids=anterior["ids"], collection_only=True)
            alterados += 1
            situacao = "alterado"
        else:
            novos += 1
            situacao = "novo"
        banco.add_embeddings(
            texts=[chunk.page_content for chunk in chunks],
            embeddings=vetores,
            # O hash vai junto: é ele que a próxima execução compara.
            metadatas=[{**chunk.metadata, "hash": hash_atual} for chunk in chunks],
            # ID estável: coleção, documento e posição do chunk no documento.
            ids=[f"{COLECAO}/{arquivo.name}#{numero}" for numero in range(len(chunks))],
        )
        gravados += len(chunks)
        print(f"{situacao}: {arquivo.name} | {len(chunks)} chunks")

    # Obsoleto: está no índice, mas o arquivo não está na pasta. Só a pasta inteira responde isso.
    if pasta_inteira:
        nomes_na_pasta = {arquivo.name for arquivo in selecionados}
        for source, anterior in no_indice.items():
            if source not in nomes_na_pasta:
                banco.delete(ids=anterior["ids"], collection_only=True)
                removidos += 1
                print(f"removido: {source} | {len(anterior['ids'])} chunks")

    print(
        f"Coleção {COLECAO} | novos {novos} | alterados {alterados} | removidos {removidos} | "
        f"iguais {iguais} | {gravados} chunks gravados"
    )


if __name__ == "__main__":
    main()
