"""Bastidor dos subagentes: o que cada um recebeu, leu e devolveu, e quando rodou.

É encanamento, fora do escopo da aula: existe para a página mostrar o lado de lá da fronteira.
Fica fora do estado do orquestrador de propósito. Se este registro entrasse no histórico dele,
o material bruto que o subagente leu subiria junto, e a demo provaria o contrário da aula.

Fica em memória: reiniciar a aplicação apaga o bastidor, e o histórico continua no PostgreSQL.
"""

from datetime import datetime

from langchain_core.messages import AIMessage, ToolMessage

# A página diz qual sessão e qual pergunta estão rodando antes de chamar o orquestrador.
sessao_atual = ""
pergunta_atual = 0

# Por sessão, a lista de chamadas de subagente na ordem em que terminaram.
registros: dict[str, list[dict]] = {}


def registrar(subagente: str, modelo: str, entrada: dict, inicio: datetime, resultado: dict) -> None:
    """Guarda o que aconteceu dentro de uma chamada de subagente."""
    mensagens = resultado["messages"]
    # O schema também chega ao modelo como ferramenta: a chamada dele não é uma busca.
    schema = type(resultado["structured_response"]).__name__
    buscas = [
        f"{chamada['name']}({', '.join(f'{chave}={valor!r}' for chave, valor in chamada['args'].items())})"
        for mensagem in mensagens
        if isinstance(mensagem, AIMessage)
        for chamada in mensagem.tool_calls
        if chamada["name"] != schema
    ]
    registros.setdefault(sessao_atual, []).append(
        {
            "pergunta": pergunta_atual,
            "subagente": subagente,
            "modelo": modelo,
            "entrada": entrada,
            "inicio": inicio,
            "fim": datetime.now(),
            "buscas": buscas,
            "chamadas_modelo": sum(isinstance(mensagem, AIMessage) for mensagem in mensagens),
            "mensagens": len(mensagens),
            "caracteres_lidos": sum(len(mensagem.text) for mensagem in mensagens if isinstance(mensagem, ToolMessage) and mensagem.name != schema),
            "caracteres_devolvidos": len(resultado["structured_response"].model_dump_json(indent=2)),
        }
    )
