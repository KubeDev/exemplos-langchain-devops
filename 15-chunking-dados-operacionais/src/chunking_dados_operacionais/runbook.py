"""Divide o runbook RB-381 por tamanho e por seção e mostra o chunk do passo 7.

Roda sem chave e sem banco: não gera embedding.
"""

from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

# Parâmetros da demo
TAMANHO = 1000  # caracteres por chunk
SOBREPOSICAO = 0  # caracteres repetidos do fim do chunk anterior; mude para 200 e rode de novo
TRECHO = "aprovação explícita"  # o passo 7 do procedimento

ARQUIVO = Path(__file__).resolve().parents[2] / "dados" / "RB-381-payments-worker.md"


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
# A demo: o chunk do passo 7, por tamanho e por seção
# ---------------------------------------------------------------------------


def mostrar(titulo: str, chunks: list[Document]) -> None:
    """Imprime só o chunk que contém o trecho procurado."""
    print(f"\n########## {titulo}: {len(chunks)} chunks")
    for numero, chunk in enumerate(chunks, start=1):
        if TRECHO in chunk.page_content:
            print(f"\n===== chunk {numero} de {len(chunks)} | {len(chunk.page_content)} caracteres")
            print(chunk.page_content)


def main() -> None:
    texto = ARQUIVO.read_text(encoding="utf-8")
    runbook = Document(page_content=texto, metadata={"source": ARQUIVO.name, "tipo": "runbook", "servico": "payments-worker"})
    mostrar(f"Por tamanho ({TAMANHO}, sobreposição {SOBREPOSICAO})", dividir_por_tamanho(runbook, TAMANHO, SOBREPOSICAO))
    mostrar("Por seção", dividir_por_secao(runbook))


if __name__ == "__main__":
    main()
