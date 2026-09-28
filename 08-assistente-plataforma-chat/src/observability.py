import json
import sys
from time import perf_counter
from typing import Any
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler

MAX_SUMMARY_LENGTH = 240
SENSITIVE_KEYS = ("api_key", "auth", "authorization", "password", "secret", "token")
SAFE_ARGUMENT_VALUES = {
    "namespace": {"kube-system"},
    "resource": {"pod", "pods"},
    "resourcetype": {"pod", "pods"},
}
SAFE_TOOL_NAMES = {
    "explain_resource",
    "kubectl_context",
    "kubectl_describe",
    "kubectl_get",
    "kubectl_logs",
    "kubectl_reconnect",
    "list_api_resources",
    "ping",
}


def _is_sensitive(key: str) -> bool:
    normalized_key = key.lower().replace("-", "_")
    return any(sensitive_key in normalized_key for sensitive_key in SENSITIVE_KEYS)


def _sanitize(value: Any, key: str = "", depth: int = 0) -> Any:
    if _is_sensitive(key):
        return "[REDACTED]"

    if isinstance(value, dict):
        if depth > 0:
            return "<objeto omitido>"
        return {
            str(item_key): _sanitize(item, str(item_key), depth + 1)
            for item_key, item in value.items()
        }

    if isinstance(value, str):
        normalized_key = key.lower().replace("-", "_").replace("_", "")
        allowed_values = SAFE_ARGUMENT_VALUES.get(normalized_key, set())
        return value if value.lower() in allowed_values else "<texto omitido>"

    if isinstance(value, (list, tuple)):
        return f"<{type(value).__name__} com {len(value)} itens>"

    if value is None or isinstance(value, (bool, int, float)):
        return f"<{type(value).__name__} omitido>"

    return f"<{type(value).__name__}>"


def _summary(value: Any) -> str:
    sanitized = _sanitize(value)
    if isinstance(sanitized, str):
        text = sanitized
    else:
        text = json.dumps(sanitized, ensure_ascii=False, default=str)

    compact = " ".join(text.split())
    if len(compact) > MAX_SUMMARY_LENGTH:
        return f"{compact[:MAX_SUMMARY_LENGTH]}…"
    return compact


def _content_summary(value: Any) -> str:
    if hasattr(value, "content"):
        value = value.content

    if isinstance(value, str):
        return f"texto com {len(value)} caracteres"
    if isinstance(value, (list, tuple)):
        return f"{type(value).__name__} com {len(value)} itens"
    if isinstance(value, dict):
        return f"objeto com {len(value)} campos"
    return f"valor do tipo {type(value).__name__}"


class DidacticObservabilityCallback(AsyncCallbackHandler):
    """Expõe eventos didáticos no terminal sem registrar conteúdo sensível."""

    def __init__(self) -> None:
        self._started_at: float | None = None
        self._model_decision = 0
        self._tool_names: dict[UUID, str] = {}

    def _log(self, message: str) -> None:
        print(f"[observabilidade] {message}", file=sys.stderr, flush=True)

    def _safe_tool_name(self, value: Any) -> str:
        tool_name = str(value or "")
        return tool_name if tool_name in SAFE_TOOL_NAMES else "<nome omitido>"

    def question_received(self, question: str) -> None:
        self._started_at = perf_counter()
        self._log(f"pergunta recebida: {len(question)} caracteres")

    async def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._model_decision += 1
        self._log(f"decisão do modelo iniciada (etapa {self._model_decision})")

    async def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        tool_name = self._safe_tool_name(serialized.get("name"))
        self._tool_names[run_id] = tool_name
        arguments = inputs if inputs is not None else input_str
        self._log(
            f"ferramenta iniciada: {tool_name}; argumentos: {_summary(arguments)}"
        )

    async def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        tool_name = self._tool_names.pop(run_id, "desconhecida")
        self._log(
            f"ferramenta finalizada: {tool_name}; "
            f"resultado: {_content_summary(output)}"
        )

    async def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        tool_name = self._tool_names.pop(run_id, "desconhecida")
        self._log(
            f"ferramenta finalizada com erro: {tool_name}; "
            f"tipo: {type(error).__name__}"
        )

    def final_answer(self, answer: str) -> None:
        duration = perf_counter() - self._started_at if self._started_at else 0.0
        self._log(f"resposta final: gerada ({len(answer)} caracteres)")
        self._log(f"duração total: {duration:.2f}s")
