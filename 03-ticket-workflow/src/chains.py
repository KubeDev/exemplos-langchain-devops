
import os
import time

from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src import logs
from src.prompts import SYSTEM_DEV, SYSTEM_INFRA, SYSTEM_TRIAGEM

# ─────────────────────────────────────────────────────────────── os modelos
#
# Um modelo por etapa: Haiku na triagem (barata, roda sempre), Sonnet nos
# analistas. Por que a assimetria: README, "Um modelo por etapa".

MODELO_TRIAGEM = os.getenv("MODELO_TRIAGEM", "claude-haiku-4-5")
MODELO_ANALISE = os.getenv("MODELO_ANALISE", "claude-sonnet-5")

# Sem `temperature` — os modelos novos removeram os parametros de sampling e
# devolvem 400. Ver README, "Tres coisas que a validacao ensinou" (1).
modelo_triagem = init_chat_model(MODELO_TRIAGEM, model_provider="anthropic")
modelo_analise = init_chat_model(MODELO_ANALISE, model_provider="anthropic")


# ─────────────────────────────────────────────────────────────── os prompts
#
# So a montagem dos templates — a primeira das tres pecas. O texto dos
# prompts vive em `prompts.py`. O `{alerta}` e a variavel que o template
# espera receber no dicionario.

prompt_triagem = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_TRIAGEM), ("human", "{alerta}")]
)
prompt_infra = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_INFRA), ("human", "{alerta}")]
)
prompt_dev = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_DEV), ("human", "{alerta}")]
)


# ──────────────────────────────────────────────────────────────── as chains
#
# Aqui esta a licao inteira. Cada chain e tres pecas ligadas por `|`:
#
#   {"alerta": "..."}  →  prompt  →  mensagens  →  modelo  →  AIMessage  →  parser  →  str

triagem = prompt_triagem | modelo_triagem | StrOutputParser()
analista_infra = prompt_infra | modelo_analise | StrOutputParser()
analista_dev = prompt_dev | modelo_analise | StrOutputParser()


# ────────────────────────────────────────────────────────────────── o fluxo
#
# Nenhuma novidade de LangChain daqui para baixo: e Python.

CATEGORIAS = {"infra", "desenvolvimento", "ambos"}


def classificar(alerta: str) -> str:
    """Chama a chain de triagem e devolve a categoria ja normalizada.

    O prompt pede DUAS linhas — raciocinio, depois a palavra (por que:
    README, "Tres coisas que a validacao ensinou", item 2). Como a saida e
    texto livre, quem parseia e voce. Duas defesas aqui: pegar a ULTIMA linha
    (o raciocinio fica acima) e cair em `ambos` se a palavra nao for
    reconhecida — assim uma resposta estranha manda o alerta para os dois
    times em vez de derrubar o fluxo.
    """
    logs.banner("triagem")
    bruto = triagem.invoke({"alerta": alerta})

    linhas = [linha for linha in bruto.strip().splitlines() if linha.strip()]
    categoria = linhas[-1].strip().lower().strip(".") if linhas else ""
    raciocinio = " ".join(linhas[:-1]).strip()

    logs.campo("modelo", MODELO_TRIAGEM)
    if raciocinio:
        logs.campo("raciocinio", raciocinio)

    if categoria not in CATEGORIAS:
        logs.campo("categoria", f"'{categoria}' nao reconhecida → usando 'ambos'")
        return "ambos"

    logs.campo("categoria", categoria)
    return categoria


def _analisar(nome: str, chain, alerta: str) -> str:
    logs.banner(nome)
    inicio = time.perf_counter()
    relatorio = chain.invoke({"alerta": alerta})
    logs.campo("modelo", MODELO_ANALISE)
    logs.campo("tempo", f"{time.perf_counter() - inicio:.1f}s")
    logs.bloco("relatorio:", relatorio)
    return relatorio


def triar(alerta: str) -> tuple[str, dict[str, str]]:
    """Classifica o alerta e aciona o(s) especialista(s) apropriado(s).

    Devolve a categoria e um dicionario {equipe: relatorio} — com uma ou duas
    entradas. Quem chama itera sobre ele sem precisar saber quantas vieram.
    """
    categoria = classificar(alerta)

    if categoria == "infra":
        return categoria, {"infra": _analisar("analista infra", analista_infra, alerta)}

    if categoria == "desenvolvimento":
        return categoria, {
            "desenvolvimento": _analisar("analista dev", analista_dev, alerta)
        }

    # "ambos": os dois especialistas analisam o mesmo alerta, um depois do
    # outro. Cada um recebe exatamente o mesmo texto — a diferenca entre os
    # relatorios vem so da lente de cada system prompt.
    return categoria, {
        "infra": _analisar("analista infra", analista_infra, alerta),
        "desenvolvimento": _analisar("analista dev", analista_dev, alerta),
    }
