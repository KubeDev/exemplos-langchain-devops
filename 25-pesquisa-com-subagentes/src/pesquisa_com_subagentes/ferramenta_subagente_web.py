"""Subagente de pesquisa na web, exposto como ferramenta do orquestrador.

O arquivo tem três partes, na ordem em que se monta um subagente:

1. o schema do que ele devolve;
2. o agente de dentro, com o próprio modelo, as próprias instruções e as próprias ferramentas;
3. a ferramenta que embrulha o agente: é ela que o orquestrador enxerga.
"""

from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_tavily import TavilySearch
from pydantic import BaseModel, Field

from pesquisa_com_subagentes.bastidor import registrar

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

MODELO = "claude-haiku-5-5"

# ---------------------------------------------------------------------------
# 1. O contrato de saída: o que sobe para o orquestrador
# ---------------------------------------------------------------------------


class PesquisaWeb(BaseModel):
    """A resposta final da pesquisa. Preencha uma vez só, depois de ler as páginas."""

    resumo: str = Field(description="A resposta à pergunta em até três frases.")
    evidencias: list[str] = Field(description="Até três fatos que sustentam o resumo, um por item.")
    fontes: list[str] = Field(description="As URLs das páginas que sustentam o resumo.")


# ---------------------------------------------------------------------------
# 2. O agente de dentro
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = f"""Você pesquisa na internet sobre DevOps, cloud e desenvolvimento.
A data de hoje é {date.today().isoformat()}.
Prefira a documentação oficial do projeto ou do fornecedor.
Responda só com o que as páginas encontradas sustentam."""

agente_web = create_agent(
    model=f"anthropic:{MODELO}",
    system_prompt=SYSTEM_PROMPT,
    # O que este subagente alcança: só a busca na web. Nada da base interna.
    tools=[TavilySearch(max_results=5)],
    # O formato da resposta final: o agente termina preenchendo o schema.
    response_format=PesquisaWeb,
    # Não herda o checkpointer do orquestrador: cada chamada começa do zero e nada fica gravado.
    checkpointer=False,
)

# ---------------------------------------------------------------------------
# 3. O embrulho: o subagente como ferramenta do orquestrador
# ---------------------------------------------------------------------------


@tool(parse_docstring=True)
def subagente_web(pergunta: str) -> str:
    """Pesquisa na internet: documentação oficial, notas de versão e boas práticas públicas.

    Use para o que é público. O que é dos projetos do time não está na internet.
    A pergunta sai do seu ambiente para um serviço de busca externo: não coloque nela dado interno.

    Args:
        pergunta: O que pesquisar, completo. O subagente não vê a conversa com o usuário.
    """
    inicio = datetime.now()
    # O argumento é a única coisa que o subagente recebe.
    resultado = agente_web.invoke({"messages": [{"role": "user", "content": pergunta}]})
    registrar("subagente_web", MODELO, {"pergunta": pergunta}, inicio, resultado)

    # Só o retorno tipado sobe. As páginas lidas ficam no histórico do subagente.
    return resultado["structured_response"].model_dump_json(indent=2)
