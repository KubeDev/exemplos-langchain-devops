from pathlib import Path

from langchain.tools import tool
from langchain_community.document_loaders import TextLoader

RUNBOOKS_PATH = Path(__file__).resolve().parent.parent / "dados" / "runbooks"
RUNBOOKS = {
    "RB-274": RUNBOOKS_PATH / "RB-274.md",
    "RB-381": RUNBOOKS_PATH / "RB-381.md",
    "RB-905": RUNBOOKS_PATH / "RB-905.md",
}


@tool
def consultar_runbook(runbook_id: str) -> str:
    """Carrega um runbook interno pelo identificador informado na pergunta.

    Args:
        runbook_id: Identificador do runbook, como RB-274, RB-381 ou RB-905.
    """
    runbook_id = runbook_id.upper()
    print(f"Ferramenta: consultar_runbook(runbook_id={runbook_id!r})")

    caminho = RUNBOOKS.get(runbook_id)

    if caminho is None:
        return f"Runbook {runbook_id} não encontrado."

    loader = TextLoader(caminho, encoding="utf-8")
    documentos = loader.load()

    return "\n\n".join(documento.page_content for documento in documentos)
