"""Carrega cada tipo de dado operacional e o divide em chunks."""

import json
from datetime import datetime, timedelta
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from pypdf import PdfReader

from .config import DATA_DIR

# ---------------------------------------------------------------------------
# Carregar: cada arquivo vira um Document inteiro, como na Aula 06
# ---------------------------------------------------------------------------


def carregar_markdown(arquivo: Path) -> Document:
    """Lê um documento Markdown e extrai tipo e serviço do cabeçalho."""
    texto = arquivo.read_text(encoding="utf-8").strip()
    metadata = {"source": arquivo.name, "tipo": "documento", "servico": "desconhecido"}
    for linha in texto.splitlines()[:10]:
        if linha.startswith("**Tipo:**"):
            metadata["tipo"] = linha.removeprefix("**Tipo:**").strip()
        if linha.startswith("**Serviço:**"):
            metadata["servico"] = linha.removeprefix("**Serviço:**").strip()
    return Document(page_content=texto, metadata=metadata)


def carregar_pdf(arquivo: Path) -> Document:
    """Extrai o texto de todas as páginas do post-mortem."""
    texto = "\n\n".join((pagina.extract_text() or "").strip() for pagina in PdfReader(arquivo).pages)
    servico = "desconhecido"
    for linha in texto.splitlines():
        if linha.startswith("Serviço:"):
            servico = linha.removeprefix("Serviço:").split()[0]
            break
    return Document(page_content=texto, metadata={"source": arquivo.name, "tipo": "post-mortem", "servico": servico})


def carregar_texto(arquivo: Path) -> Document:
    """Lê qualquer arquivo como texto puro, sem interpretar sua estrutura."""
    return Document(page_content=arquivo.read_text(encoding="utf-8"), metadata={"source": arquivo.name, "tipo": "texto"})


def carregar_eventos(arquivo: Path) -> list[dict]:
    """Lê um log JSON Lines: um evento por linha."""
    return [json.loads(linha) for linha in arquivo.read_text(encoding="utf-8").splitlines() if linha.strip()]


def carregar_tickets(arquivo: Path) -> list[dict]:
    """Lê a exportação de tickets do sistema de chamados."""
    return json.loads(arquivo.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Dividir: uma função por estratégia
# ---------------------------------------------------------------------------


def dividir_por_tamanho(documento: Document, tamanho: int, sobreposicao: int) -> list[Document]:
    """Recursivo: tenta parágrafo, depois linha, depois palavra, até caber no tamanho."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=tamanho, chunk_overlap=sobreposicao, add_start_index=True)
    return splitter.split_documents([documento])


def dividir_por_secao(documento: Document, tamanho: int, sobreposicao: int) -> list[Document]:
    """Estrutura: corta nos títulos Markdown e só divide por tamanho a seção que não couber."""
    titulos = [("#", "h1"), ("##", "h2"), ("###", "h3")]
    secoes = MarkdownHeaderTextSplitter(headers_to_split_on=titulos).split_text(documento.page_content)
    splitter = RecursiveCharacterTextSplitter(chunk_size=tamanho, chunk_overlap=sobreposicao)

    chunks = []
    for secao in secoes:
        caminho = " > ".join(secao.metadata[nivel] for _, nivel in titulos if nivel in secao.metadata)
        contexto = f"[{documento.metadata['servico']} | {documento.metadata['tipo']}] {caminho}"
        for pedaco in splitter.split_text(secao.page_content):
            # O título vai junto no texto: um "passo 4" sozinho não diz de qual procedimento é.
            chunks.append(
                Document(
                    page_content=f"{contexto}\n\n{pedaco}",
                    metadata={**documento.metadata, "secao": caminho},
                )
            )
    return chunks


def horario(evento: dict) -> datetime:
    """Converte o timestamp ISO 8601 do evento."""
    return datetime.fromisoformat(evento["timestamp"].replace("Z", "+00:00"))


def renderizar_evento(evento: dict) -> str:
    """Transforma o JSON do evento numa linha legível: só o que tem significado vai para o embedding."""
    linha = f"{evento['timestamp'][11:23]} {evento['level']} {evento['pod']} {evento['message']}"
    if evento.get("exception"):
        linha += "\n" + evento["exception"]
    return linha


def janelas_de_log(eventos: list[dict], fonte: str, segundos: int, sobreposicao: int) -> list[Document]:
    """Janela de tempo: agrupa os eventos de cada serviço em intervalos fixos do relógio."""
    # O que indexar: INFO e DEBUG são volume, não evidência. Ficam no sistema de logs.
    relevantes = [evento for evento in eventos if evento["level"] in ("WARN", "ERROR")]

    chunks = []
    # Uma janela nunca mistura serviços.
    for servico in sorted({evento["service"] for evento in relevantes}):
        do_servico = [evento for evento in relevantes if evento["service"] == servico]
        primeiro = horario(do_servico[0])
        inicio = primeiro - timedelta(seconds=primeiro.timestamp() % segundos)
        fim = horario(do_servico[-1])

        while inicio <= fim:
            limite = inicio + timedelta(seconds=segundos)
            na_janela = [evento for evento in do_servico if inicio <= horario(evento) < limite]
            if na_janela:
                chunks.append(
                    Document(
                        page_content=f"[{servico} | log] {inicio:%H:%M:%S} a {limite:%H:%M:%S}\n\n"
                        + "\n".join(renderizar_evento(evento) for evento in na_janela),
                        metadata={
                            "source": fonte,
                            "tipo": "log",
                            "servico": servico,
                            "inicio": inicio.isoformat(),
                            "fim": limite.isoformat(),
                            "trace_ids": sorted({e["trace_id"] for e in na_janela if e.get("trace_id")}),
                        },
                    )
                )
            # Sem sobreposição, a próxima janela começa onde esta terminou.
            inicio += timedelta(seconds=segundos - sobreposicao)
    return chunks


def dividir_tickets(tickets: list[dict], fonte: str, tamanho: int) -> list[Document]:
    """Registro: um ticket por chunk; os campos viram metadado, o texto vira conteúdo."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=tamanho, chunk_overlap=0)
    chunks = []
    for ticket in tickets:
        cabecalho = f"[{ticket['servico']} | ticket] {ticket['id']}: {ticket['titulo']}"
        corpo = ticket["descricao"] + "\n\n" + "\n\n".join(
            f"{comentario['em']} | {comentario['autor']}: {comentario['texto']}" for comentario in ticket["comentarios"]
        )
        metadata = {
            "source": fonte,
            "tipo": "ticket",
            "servico": ticket["servico"],
            "ticket": ticket["id"],
            "severidade": ticket["severidade"],
            "status": ticket["status"],
        }
        # Ticket com histórico longo é dividido, mas cada pedaço leva o cabeçalho do ticket.
        for pedaco in splitter.split_text(corpo):
            chunks.append(Document(page_content=f"{cabecalho}\n\n{pedaco}", metadata=metadata))
    return chunks


# ---------------------------------------------------------------------------
# As duas configurações comparadas na aula
# ---------------------------------------------------------------------------


def configuracao_a() -> list[Document]:
    """A: tudo como texto, recursivo com o mesmo tamanho e sobreposição."""
    chunks = []
    for arquivo in sorted(DATA_DIR.glob("*.md")):
        chunks += dividir_por_tamanho(carregar_markdown(arquivo), tamanho=1000, sobreposicao=150)
    for arquivo in sorted(DATA_DIR.glob("*.pdf")):
        chunks += dividir_por_tamanho(carregar_pdf(arquivo), tamanho=1000, sobreposicao=150)
    for arquivo in sorted(DATA_DIR.glob("logs/*.jsonl")):
        chunks += dividir_por_tamanho(carregar_texto(arquivo), tamanho=1000, sobreposicao=150)
    chunks += dividir_por_tamanho(carregar_texto(DATA_DIR / "tickets.json"), tamanho=1000, sobreposicao=150)
    return chunks


def configuracao_b() -> list[Document]:
    """B: a estratégia segue a natureza de cada dado."""
    chunks = []
    for arquivo in sorted(DATA_DIR.glob("*.md")):
        chunks += dividir_por_secao(carregar_markdown(arquivo), tamanho=3500, sobreposicao=0)
    for arquivo in sorted(DATA_DIR.glob("*.pdf")):
        chunks += dividir_por_tamanho(carregar_pdf(arquivo), tamanho=2000, sobreposicao=0)
    for arquivo in sorted(DATA_DIR.glob("logs/*.jsonl")):
        chunks += janelas_de_log(carregar_eventos(arquivo), arquivo.name, segundos=60, sobreposicao=20)
    chunks += dividir_tickets(carregar_tickets(DATA_DIR / "tickets.json"), "tickets.json", tamanho=1500)
    return chunks
