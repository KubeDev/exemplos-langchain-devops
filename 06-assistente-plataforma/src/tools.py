import os

from dotenv import load_dotenv

load_dotenv()

KUBERNETES_MCP_TOKEN = os.getenv("KUBERNETES_MCP_TOKEN")

if not KUBERNETES_MCP_TOKEN:
    raise SystemExit("Configure KUBERNETES_MCP_TOKEN no arquivo .env antes de executar.")

MCP_CONFIG = {
    "mcpServers": {
        "kubernetes": {
            "transport": "http",
            "url": os.getenv(
                "KUBERNETES_MCP_URL", "http://127.0.0.1:3001/mcp"
            ),
            "headers": {"X-MCP-AUTH": KUBERNETES_MCP_TOKEN},
        }
    }
}
