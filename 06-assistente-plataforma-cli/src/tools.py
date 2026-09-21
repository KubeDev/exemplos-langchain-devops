import os


class ConfigurationError(Exception):
    """Erro de configuração com mensagem segura definida pela aplicação."""


def mcp_config() -> dict:
    token = os.getenv("KUBERNETES_MCP_TOKEN")
    if not token:
        raise ConfigurationError(
            "Configure KUBERNETES_MCP_TOKEN no arquivo .env antes de executar."
        )

    return {
        "mcpServers": {
            "kubernetes": {
                "transport": "http",
                "url": os.getenv(
                    "KUBERNETES_MCP_URL", "http://127.0.0.1:3001/mcp"
                ),
                "headers": {"X-MCP-AUTH": token},
            }
        }
    }
