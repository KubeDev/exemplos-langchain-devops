import re

from langchain.agents.middleware import PIIMatch, PIIMiddleware


# Detector como função: recebe o texto e devolve onde está cada ocorrência.
# Por dentro, aqui, é uma expressão regular; poderia ser qualquer lógica.
def detectar_chave_ssh(conteudo: str) -> list[PIIMatch]:
    """Encontra chaves SSH privadas no texto, do BEGIN até o END."""
    # re.DOTALL: o ".*?" também atravessa as quebras de linha da chave.
    padrao = r"-----BEGIN .*?PRIVATE KEY-----.*?-----END .*?PRIVATE KEY-----"

    encontrados = []
    for chave in re.finditer(padrao, conteudo, re.DOTALL):
        encontrados.append(
            PIIMatch(
                type="chave_ssh",  # nome do dado
                value=chave.group(),  # o texto encontrado
                start=chave.start(),  # onde começa no conteúdo
                end=chave.end(),  # onde termina no conteúdo
            )
        )
    return encontrados


# Um PIIMiddleware por dado sensível: o tipo, como detectar, o que fazer e onde verificar.
GUARDRAILS = [
    # Entrada do usuário: o token colado no chat chega ao modelo mascarado.
    PIIMiddleware(
        "token_digitalocean",
        detector=r"dop_v1_[a-f0-9]{64}",
        strategy="mask",  # "block" interrompe a execução antes do modelo
        apply_to_input=True,  # já é o padrão; explícito para a leitura
    ),
    # Retorno da ferramenta: a chave SSH sai do resultado antes de o modelo ler.
    PIIMiddleware(
        "chave_ssh",
        detector=detectar_chave_ssh,
        strategy="redact",
        apply_to_input=False,
        apply_to_tool_results=True,
    ),
    # Retorno da ferramenta: tipo pronto, sem detector próprio.
    PIIMiddleware(
        "email",
        strategy="mask",
        apply_to_input=False,
        apply_to_tool_results=True,
    ),
    # Resposta do modelo: só a senha da connection string, entre ":" e "@".
    # O modelo já leu a senha; o que sai limpo é a resposta.
    PIIMiddleware(
        "senha_banco",
        detector=r"(?<=:)[^:@/\s]+(?=@)",
        strategy="hash",
        apply_to_input=False,
        apply_to_output=True,
    ),
]
