from langchain.tools import tool

# Dados simulados: o que um `kubectl describe`, um `terraform show` ou um log de deploy
# devolveriam. Os segredos vêm no meio da informação de sistema, de propósito, e são
# todos fictícios.
APLICACOES = {
    "kube-news": """\
aplicação: kube-news
stack: Node.js 20 · Express · PostgreSQL 16
porta: 8080
responsável: plataforma@kubenews.dev
banco: DATABASE_URL=postgresql://kubenews:Kn3wsPg2026@db-kube-news:5432/kubenews
acesso ao servidor (chave SSH):
-----BEGIN OPENSSH PRIVATE KEY-----
AAAAexemploFICTICIOdeCHAVEparaAULAkubeNEWSnaoUSEemNADAaaaaAAAAbbbbBBBB
ccccCCCCddddDDDDeeeeEEEEffffFFFFgggg0000111122223333444455556666777788
-----END OPENSSH PRIVATE KEY-----
status: em execução, 2 instâncias saudáveis
""",
    "encontros-tech": """\
aplicação: encontros-tech
stack: Python 3.12 · Flask · Gunicorn · PostgreSQL 16
porta: 8000
responsável: eventos@encontros.tech
banco: DATABASE_URL=postgresql://encontros:Enc0ntrosDb26@db-encontros:5432/encontros
acesso ao servidor (chave SSH):
-----BEGIN OPENSSH PRIVATE KEY-----
AAAAexemploFICTICIOdeCHAVEparaAULAencontrosTECHnaoUSEemNADAaaaaAAAAbbbb
ccccCCCCddddDDDDeeeeEEEEffffFFFFgggg9999888877776666555544443333222211
-----END OPENSSH PRIVATE KEY-----
status: em execução, 1 instância saudável
""",
}


@tool
def consultar_aplicacao(nome: str) -> str:
    """Consulta a configuração e o estado de uma aplicação da plataforma.

    Args:
        nome: Nome da aplicação, como kube-news ou encontros-tech.
    """
    return APLICACOES.get(nome, f"Não tenho informações sobre a aplicação {nome}.")
