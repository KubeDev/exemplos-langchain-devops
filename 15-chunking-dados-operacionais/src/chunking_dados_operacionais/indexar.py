"""Divide a base pela natureza de cada dado, gera embeddings e reconstrói a coleção.

As funções de divisão são as mesmas de gerar_chunks.py, copiadas de propósito: cada arquivo se
lê sozinho, sem navegar entre arquivos. Ao mudar uma estratégia, mude nos dois lugares.
"""

import os
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "dados"
COLECAO = "chunks"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536

# A chave da OpenAI e a conexão do banco vêm do .env.
load_dotenv(ROOT / ".env")

# ---------------------------------------------------------------------------
# Documentos: recursivo e por seção (as mesmas funções de gerar_chunks.py)
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


def dividir_recursivo(documento: Document, tamanho: int, sobreposicao: int) -> list[Document]:
    """Recursivo: tenta o parágrafo; se não couber, a linha; depois a palavra."""
    # Respeita o tamanho; corta na palavra só quando um parágrafo passa do tamanho.
    splitter = RecursiveCharacterTextSplitter(chunk_size=tamanho, chunk_overlap=sobreposicao)
    return splitter.split_documents([documento])


def dividir_por_secao(documento: Document) -> list[Document]:
    """Seção: corta nos títulos Markdown e põe o título no texto do chunk."""
    # Sem limite de tamanho: nesta base a maior seção tem cerca de 5 mil caracteres.
    # Se uma seção passar do limite do modelo de embedding, divida essa seção pelo recursivo.
    titulos = [("#", "h1"), ("##", "h2"), ("###", "h3")]
    # Este splitter só aceita texto: o metadado do documento é recolocado logo abaixo.
    secoes = MarkdownHeaderTextSplitter(headers_to_split_on=titulos).split_text(documento.page_content)

    servico = documento.metadata["servico"]
    tipo = documento.metadata["tipo"]
    chunks = []
    for secao in secoes:
        # Os títulos acima da seção, ex.: "RB-381 - Fila parada... > Procedimento de estabilização"
        caminho = " > ".join(secao.metadata.values())
        # Um "passo 4" sozinho não diz de qual procedimento é: o título vai junto no texto.
        # Ex.: "[payments-worker | runbook] RB-381 - ... > Procedimento de estabilização"
        texto = f"[{servico} | {tipo}] {caminho}\n\n{secao.page_content}"
        # O metadado do documento, mais a seção.
        metadata = dict(documento.metadata)
        metadata["secao"] = caminho
        chunks.append(Document(page_content=texto, metadata=metadata))
    return chunks


# ---------------------------------------------------------------------------
# A base inteira: a estratégia segue a natureza de cada dado
# ---------------------------------------------------------------------------


def dividir_base() -> list[Document]:
    """Divide todos os dados da pasta dados/ com a estratégia de cada tipo."""
    chunks = []
    # Markdown tem títulos: cada seção vira um chunk.
    for arquivo in sorted(DATA_DIR.glob("*.md")):
        chunks += dividir_por_secao(carregar_markdown(arquivo))
    # O PDF perde os títulos na extração. 1000 e 200 são ponto de partida, não medição.
    for arquivo in sorted(DATA_DIR.glob("*.pdf")):
        chunks += dividir_recursivo(carregar_pdf(arquivo), tamanho=1000, sobreposicao=200)
    return chunks


def main() -> None:
    """Indexa todos os chunks da base numa coleção do pgvector."""
    chunks = dividir_base()

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
