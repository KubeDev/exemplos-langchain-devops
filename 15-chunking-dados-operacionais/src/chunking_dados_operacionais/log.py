"""Divide o log em janelas de tempo e mostra o início do incidente no payments-worker.

Roda sem chave e sem banco: não gera embedding.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from langchain_core.documents import Document

# Parâmetros da demo
SEGUNDOS = 15  # duração de cada janela
SOBREPOSICAO = 0  # segundos repetidos do fim da janela anterior; mude para 5 e rode de novo
TRECHO = "14:04:1"  # o início do incidente: qualquer horário de 14:04:10 a 14:04:19

ARQUIVO = Path(__file__).resolve().parents[2] / "dados" / "logs" / "payments-worker.jsonl"


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
# A demo: as janelas do início do incidente
# ---------------------------------------------------------------------------


def main() -> None:
    janelas = janelas_de_log(ARQUIVO, SEGUNDOS, SOBREPOSICAO)
    for numero, janela in enumerate(janelas, start=1):
        if TRECHO in janela.page_content:
            print(f"\n===== janela {numero} de {len(janelas)} | {len(janela.page_content)} caracteres")
            print(janela.page_content)

    caracteres = sum(len(janela.page_content) for janela in janelas)
    print(f"\nJanela de {SEGUNDOS}s, sobreposição {SOBREPOSICAO}s: {len(janelas)} chunks | {caracteres} caracteres")


if __name__ == "__main__":
    main()
