"""Divide o runbook RB-381 com duas estratégias e mostra um resumo de cada uma.

Só divide e mostra no terminal: não gera embedding nem grava no banco. Roda sem chave e sem banco.
A ordem é a da aula: o recursivo nos dois pontos de partida, depois a seção.
"""

from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

# Pontos de partida do recursivo, em caracteres; a sobreposição é 20% do tamanho.
# Resposta curta (um valor, uma configuração): chunk menor, mais preciso.
TAMANHO_CURTO = 1000
SOBREPOSICAO_CURTO = 200
# Resposta longa (um procedimento, uma linha do tempo): chunk maior, mais contexto.
TAMANHO_LONGO = 2000
SOBREPOSICAO_LONGO = 400

ARQUIVO = Path(__file__).resolve().parents[2] / "dados" / "RB-381-payments-worker.md"


def dividir_recursivo(documento: Document, tamanho: int, sobreposicao: int) -> list[Document]:
    """Recursivo: tenta o parágrafo; se não couber, a linha; depois a palavra."""
    # Respeita o tamanho; corta na palavra só quando um parágrafo passa do tamanho.
    # É o que corta os post-mortems em PDF no indexar.
    splitter = RecursiveCharacterTextSplitter(chunk_size=tamanho, chunk_overlap=sobreposicao)
    return splitter.split_documents([documento])


def dividir_por_secao(documento: Document) -> list[Document]:
    """3. Seção: corta nos títulos Markdown e põe o título no texto do chunk."""
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
# A demo: uma linha de resumo por estratégia
# ---------------------------------------------------------------------------


def repetido(anterior: str, atual: str) -> int:
    """Quantos caracteres do fim do chunk anterior reaparecem no começo deste: a sobreposição."""
    # Testa do maior começo possível para o menor; o primeiro que bate é a sobreposição.
    for tamanho in range(len(atual), 0, -1):
        comeco = atual[:tamanho]
        if anterior.endswith(comeco):
            return tamanho
    return 0


def mostrar(titulo: str, chunks: list[Document]) -> None:
    """Imprime quantos chunks saíram, o menor, o maior, o total e quanto texto foi repetido."""
    tamanhos = []
    repetidos = 0
    anterior = ""
    for chunk in chunks:
        tamanhos.append(len(chunk.page_content))
        repetidos += repetido(anterior, chunk.page_content)
        anterior = chunk.page_content
    print(f"{titulo}: {len(chunks)} chunks | menor {min(tamanhos)} | maior {max(tamanhos)}"
          f" | total {sum(tamanhos)} caracteres | {repetidos} repetidos (sobreposição)")


def main() -> None:
    texto = ARQUIVO.read_text(encoding="utf-8")
    runbook = Document(page_content=texto, metadata={"source": ARQUIVO.name, "tipo": "runbook", "servico": "payments-worker"})
    mostrar(f"1. Recursivo {TAMANHO_CURTO}/{SOBREPOSICAO_CURTO}",
            dividir_recursivo(runbook, TAMANHO_CURTO, SOBREPOSICAO_CURTO))
    mostrar(f"2. Recursivo {TAMANHO_LONGO}/{SOBREPOSICAO_LONGO}",
            dividir_recursivo(runbook, TAMANHO_LONGO, SOBREPOSICAO_LONGO))
    mostrar("3. Seção", dividir_por_secao(runbook))


if __name__ == "__main__":
    main()
