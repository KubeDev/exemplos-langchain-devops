from collections.abc import AsyncIterator
from typing import Any


def text_from_stream_part(part: dict[str, Any]) -> str:
    """Retorna somente texto do modelo; eventos de ferramenta nunca chegam à UI."""
    if part.get("type") != "messages":
        return ""

    token, metadata = part["data"]
    if metadata.get("langgraph_node") != "model":
        return ""

    return token.text


async def stream_agent_text(
    agent: Any,
    messages: list[dict[str, str]],
) -> AsyncIterator[str]:
    async for part in agent.astream(
        {"messages": messages},
        stream_mode="messages",
        version="v2",
    ):
        text = text_from_stream_part(part)
        if text:
            yield text
