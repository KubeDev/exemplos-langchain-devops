"""Divide a base pela natureza de cada dado, gera embeddings e reconstrói a coleção.

As funções de divisão são as mesmas de runbook.py e log.py, copiadas de propósito: cada arquivo se
lê sozinho, sem navegar entre arquivos. Ao mudar uma estratégia, mude nos dois lugares.
"""

import json
import os
from collections import Counter
from datetime import UTC, datetime
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
# Documentos: por tamanho e por seção (as mesmas funções de runbook.py)
# ---------------------------------------------------------------------------

# O nome do arquivo diz o tipo e o serviço: RB-381-payments-worker.md é um runbook do payments-worker.
TIPOS = {"RB": "runbook", "ARQ": "arquitetura", "REF": "referência", "PM": "post-mortem"}
SERVICOS = ["catalog-api", "payments-worker", "image-processor"]


def metadados(arquivo: Path) -> dict:
    """Monta o metadado do documento a partir do nome do arquivo."""
    tipo = TIPOS[arquivo.name.split("-")[0]]
    servico = [nome for nome in SERVICOS if nome in arquivo.name][0]
    return {"source": arquivo.name, "tipo": tipo, "servico": servico}


def carregar_markdown(arquivo: Path) -> Document:
    """Lê o documento Markdown inteiro."""
    return Document(page_content=arquivo.read_text(encoding="utf-8"), metadata=metadados(arquivo))


def carregar_pdf(arquivo: Path) -> Document:
    """Extrai o texto de todas as páginas do post-mortem."""
    texto = "\n\n".join(pagina.extract_text() for pagina in PdfReader(arquivo).pages)
    return Document(page_content=texto, metadata=metadados(arquivo))


def dividir_por_tamanho(documento: Document, tamanho: int, sobreposicao: int) -> list[Document]:
    """Por tamanho: corta o texto em pedaços de até `tamanho` caracteres."""
    # Prefere cortar entre parágrafos, depois entre linhas, depois entre palavras.
    # Para usar outro caractere de separação, informe `separators`.
    splitter = RecursiveCharacterTextSplitter(chunk_size=tamanho, chunk_overlap=sobreposicao)
    return splitter.split_documents([documento])


def dividir_por_secao(documento: Document) -> list[Document]:
    """Por seção: corta nos títulos Markdown e põe o título no texto do chunk."""
    # Sem limite de tamanho: nesta base a maior seção tem cerca de 5 mil caracteres.
    # Se uma seção passar do limite do modelo de embedding, divida essa seção por tamanho.
    titulos = [("#", "h1"), ("##", "h2"), ("###", "h3")]
    secoes = MarkdownHeaderTextSplitter(headers_to_split_on=titulos).split_text(documento.page_content)

    chunks = []
    for secao in secoes:
        # Os títulos acima da seção, ex.: "RB-381 - Fila parada... > Procedimento de estabilização"
        caminho = " > ".join(secao.metadata[nivel] for _, nivel in titulos if nivel in secao.metadata)
        # Um "passo 4" sozinho não diz de qual procedimento é: o título vai junto no texto.
        # Ex.: "[payments-worker | runbook] RB-381 - ... > Procedimento de estabilização"
        texto = f"[{documento.metadata['servico']} | {documento.metadata['tipo']}] {caminho}\n\n{secao.page_content}"
        # O metadado do documento, mais a seção.
        metadata = {**documento.metadata, "secao": caminho}
        chunks.append(Document(page_content=texto, metadata=metadata))
    return chunks


# ---------------------------------------------------------------------------
# Log: janela de tempo (as mesmas funções de log.py)
# ---------------------------------------------------------------------------


def relogio(segundos: int) -> datetime:
    """Converte segundos desde 1970 de volta em data e hora."""
    return datetime.fromtimestamp(segundos, UTC)


def renderizar_evento(evento: dict) -> str:
    """Transforma o JSON do evento numa linha legível: só o que tem significado vai para o embedding."""
    # [11:23] fica só com HH:MM:SS.mmm do timestamp ISO
    linha = f"{evento['timestamp'][11:23]} {evento['level']} {evento['pod']} {evento['message']}"
    if evento.get("exception"):
        linha += "\n" + evento["exception"]
    return linha


def janelas_de_log(arquivo: Path, segundos: int, sobreposicao: int) -> list[Document]:
    """Janela de tempo: junta os eventos que aconteceram no mesmo intervalo."""
    servico = arquivo.stem  # um arquivo de log por serviço: a janela nunca mistura serviços

    eventos = []
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        evento = json.loads(linha)
        # O que indexar: INFO e DEBUG são volume, não evidência. Ficam no sistema de logs.
        if evento["level"] in ("WARN", "ERROR"):
            evento["segundo"] = datetime.fromisoformat(evento["timestamp"]).timestamp()
            eventos.append(evento)

    primeiro = int(eventos[0]["segundo"])
    ultimo = int(eventos[-1]["segundo"])
    # A primeira janela começa num horário redondo: com janela de 15, 14:04:12 vira 14:04:00.
    primeiro = primeiro - primeiro % segundos

    chunks = []
    # Sem sobreposição, cada janela começa onde a anterior terminou.
    # Com 15 e 5, uma janela nova começa a cada 10 segundos.
    passo = segundos - sobreposicao
    for inicio in range(primeiro, ultimo + 1, passo):
        fim = inicio + segundos
        na_janela = [evento for evento in eventos if inicio <= evento["segundo"] < fim]
        if not na_janela:
            continue
        texto = f"[{servico} | log] {relogio(inicio):%H:%M:%S} a {relogio(fim):%H:%M:%S}\n\n"
        texto += "\n".join(renderizar_evento(evento) for evento in na_janela)
        metadata = {
            "source": arquivo.name,
            "tipo": "log",
            "servico": servico,
            "inicio": relogio(inicio).isoformat(),
            "fim": relogio(fim).isoformat(),
        }
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
        chunks += dividir_por_tamanho(carregar_pdf(arquivo), tamanho=1000, sobreposicao=200)
    # Janela e sobreposição do log são hipótese: só um teste de busca diz se pagam.
    for arquivo in sorted(DATA_DIR.glob("logs/*.jsonl")):
        chunks += janelas_de_log(arquivo, segundos=60, sobreposicao=20)
    return chunks


def main() -> None:
    """Indexa todos os chunks da base numa coleção do pgvector."""
    chunks = dividir_base()

    por_tipo = Counter(chunk.metadata["tipo"] for chunk in chunks)
    for tipo, quantidade in sorted(por_tipo.items()):
        # O maior chunk de cada tipo é a medição: ele precisa caber no limite do modelo de embedding.
        maior = max(len(chunk.page_content) for chunk in chunks if chunk.metadata["tipo"] == tipo)
        print(f"{tipo:>12}: {quantidade} chunks | maior com {maior} caracteres")
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
