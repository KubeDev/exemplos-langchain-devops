"""A casca HTTP.

Fina de proposito. O FastAPI valida o corpo contra o schema `Alerta`, chama
`triar()` e grava os tickets. Toda a logica esta em `chains.py` — trocar este
webhook por um consumidor de fila nao mudaria uma linha das chains.

O endpoint e `def`, nao `async def`: as chains sao sincronas, e o FastAPI roda
funcoes sincronas num pool de threads sozinho. Nao ha `async`/`await` em lugar
nenhum deste exemplo.
"""

import time
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI

# O .env tem de ser lido ANTES de importar `src.chains`: aquele modulo cria os
# modelos no proprio import, e o cliente da Anthropic captura a
# ANTHROPIC_API_KEY nesse instante. Carregar depois nao adianta — o modelo ja
# teria nascido com a chave vazia.
load_dotenv()

from src import logs, tickets
from src.chains import triar
from src.schemas import Alerta

logs.configurar()

app = FastAPI(
    title="Triagem de incidentes",
    description="Exemplo didatico de LangChain: chains com LCEL (prompt | modelo | parser).",
)


@app.post("/webhook/alerta")
def receber_alerta(alerta: Alerta) -> dict[str, Any]:
    inicio = time.perf_counter()

    logs.caixa(f"ALERTA RECEBIDO · {alerta.titulo[:44]}")
    logs.campo("servico", alerta.servico)
    logs.campo("linhas de log", len(alerta.logs))

    # A fronteira: daqui para dentro o exemplo so lida com texto.
    texto = alerta.como_texto()
    logs.bloco("enviado aos prompts:", texto)

    categoria, relatorios = triar(texto)

    logs.banner("gravar tickets")
    logs.campo("relatorios", len(relatorios))
    arquivos = tickets.gravar(alerta, categoria, relatorios)

    duracao = time.perf_counter() - inicio
    logs.resumo(" + ".join(sorted(relatorios)), arquivos, duracao)

    return {
        "categoria": categoria,
        "equipes": sorted(relatorios),
        "tickets": arquivos,
        "duracao_s": round(duracao, 1),
    }


@app.get("/saude")
def saude() -> dict[str, str]:
    return {"status": "ok"}
