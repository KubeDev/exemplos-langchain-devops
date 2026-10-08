from langchain.tools import tool

from src.droplets import consultar_droplets
from src.saude import consultar_saude


@tool
def listar_droplets(regiao: str | None = None) -> str:
    """Lista os Droplets da conta DigitalOcean com o status de cada um: active, off, new, archive.

    Use para saber quais Droplets existem e se estão ligados ou desligados, mesmo quando a
    pergunta fala em situação ou estado. Não use para saber se um Droplet ligado está
    sobrecarregado ou com desempenho ruim: para isso, use verificar_saude.

    Args:
        regiao: Slug da região em minúsculas, como nyc1. Sem região, considera todos.
    """
    return consultar_droplets(regiao, None, None, None)


@tool
def verificar_saude(regiao: str | None = None) -> str:
    """Verifica a saúde dos Droplets pelo Monitoring: load average de 1 minuto nos últimos 10 minutos.

    Use só quando a pergunta for sobre saúde, carga, CPU ou desempenho de um Droplet ligado.
    Não use para saber se o Droplet existe nem se está ligado ou desligado: para isso, use
    listar_droplets.

    Args:
        regiao: Slug da região em minúsculas, como nyc1. Sem região, considera todos.
    """
    return consultar_saude(regiao)
