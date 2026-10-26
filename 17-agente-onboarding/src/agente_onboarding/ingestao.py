"""Ingestão: o documento Markdown vira chunks com metadado, que viram embeddings no pgvector.

É o papel que escreve no índice. O agente (agente.py) só lê. A página que recebe os arquivos
está em web.py. Cada documento traz no cabeçalho (frontmatter)
o projeto e o tipo, e esses dois campos viram metadado de cada chunk: é por eles que o agente
filtra a busca depois.

Atualizar um documento é enviar de novo um arquivo com o mesmo nome: os chunks antigos dele
saem e os novos entram. O nome do arquivo é o identificador do documento.
"""

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import MarkdownHeaderTextSplitter

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
COLECAO = os.environ["COLECAO"]

EMBEDDING_MODEL = "qwen3-embedding:0.6b"
# Tamanho do vetor que o modelo gera (está na documentação dele). O pgvector precisa
# desse número para criar a coluna vector(N); trocar de modelo exige reindexar.
EMBEDDING_DIMENSIONS = 1024

# Valores aceitos no frontmatter. Documento com outro valor é recusado.
PROJETOS = ["geral", "kube-news", "encontros-tech"]
TIPOS = ["guia", "referencia", "runbook", "post-mortem"]

# ---------------------------------------------------------------------------
# Documento: cabeçalho e chunks
# ---------------------------------------------------------------------------


def ler_frontmatter(texto: str) -> tuple[dict, str]:
    """Separa o cabeçalho entre as linhas --- do corpo do documento."""
    _, cabecalho, corpo = texto.split("---\n", 2)
    campos = {}
    for linha in cabecalho.strip().splitlines():
        chave, valor = linha.split(":", 1)
        campos[chave.strip()] = valor.strip()
    return campos, corpo


def dividir(nome: str, campos: dict, corpo: str) -> list[Document]:
    """Um chunk por seção do Markdown, com o projeto, o tipo e o título no texto do chunk."""
    titulos = [("#", "h1"), ("##", "h2")]
    secoes = MarkdownHeaderTextSplitter(headers_to_split_on=titulos).split_text(corpo)

    chunks = []
    for secao in secoes:
        caminho = " > ".join(secao.metadata.values())
        texto = f"[{campos['projeto']} | {campos['tipo']}] {caminho}\n\n{secao.page_content}"
        metadado = {"source": nome, "projeto": campos["projeto"], "tipo": campos["tipo"], "secao": caminho}
        chunks.append(Document(page_content=texto, metadata=metadado))
    return chunks


# ---------------------------------------------------------------------------
# Índice: o que já está gravado e a gravação de um documento
# ---------------------------------------------------------------------------


# A coleção do pgvector, criada uma vez: as tabelas nascem aqui se o banco estiver vazio.
banco = PGVector(
    embeddings=OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=os.environ["OLLAMA_URL"]),
    # O LangChain usa o driver psycopg: a URL precisa dizer isso.
    connection=os.environ["DATABASE_URL"].replace("postgresql://", "postgresql+psycopg://", 1),
    collection_name=COLECAO,
    embedding_length=EMBEDDING_DIMENSIONS,
    use_jsonb=True,
)


def documentos_no_indice() -> dict[str, dict]:
    """Lê do banco, por documento, o projeto, o tipo e os IDs dos chunks gravados."""
    try:
        with psycopg.connect(os.environ["DATABASE_URL"]) as conexao:
            linhas = conexao.execute(
                """
                SELECT e.id, e.cmetadata->>'source', e.cmetadata->>'projeto', e.cmetadata->>'tipo'
                FROM langchain_pg_embedding e
                JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                WHERE c.name = %s
                ORDER BY 2, 1
                """,
                (COLECAO,),
            ).fetchall()
    except psycopg.errors.UndefinedTable:
        # Banco vazio: as tabelas nascem na primeira gravação.
        return {}

    documentos = {}
    for id_chunk, source, projeto, tipo in linhas:
        documento = documentos.setdefault(source, {"projeto": projeto, "tipo": tipo, "ids": []})
        documento["ids"].append(id_chunk)
    return documentos


def gravar(nome: str, texto: str) -> str:
    """Grava um documento no índice, trocando os chunks antigos dele pelos novos."""
    try:
        campos, corpo = ler_frontmatter(texto)
    except ValueError:
        return f"recusado: {nome} | sem frontmatter entre linhas ---"
    if campos.get("projeto") not in PROJETOS or campos.get("tipo") not in TIPOS:
        return f"recusado: {nome} | projeto deve ser um de {PROJETOS} e tipo um de {TIPOS}"

    chunks = dividir(nome, campos, corpo)

    # Documento já indexado: os chunks antigos saem antes de os novos entrarem.
    anterior = documentos_no_indice().get(nome)
    if anterior:
        banco.delete(ids=anterior["ids"], collection_only=True)

    # O ID leva a coleção, o documento e a posição do chunk: é único na tabela inteira.
    banco.add_documents(chunks, ids=[f"{COLECAO}/{nome}#{numero}" for numero in range(len(chunks))])

    situacao = "atualizado" if anterior else "novo"
    print(f"{situacao}: {nome} | {campos['projeto']} | {campos['tipo']} | {len(chunks)} chunks")
    return f"{situacao}: {nome} | {len(chunks)} chunks"
