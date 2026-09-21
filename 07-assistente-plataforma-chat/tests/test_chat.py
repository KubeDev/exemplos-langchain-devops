import asyncio
import unittest
from contextlib import redirect_stderr
from io import StringIO
from uuid import uuid4

from src.chat import stream_agent_text, text_from_stream_part
from src.observability import DidacticObservabilityCallback


class FakeToken:
    def __init__(self, text: str) -> None:
        self.text = text


class FakeAgent:
    def __init__(self, parts: list[dict]) -> None:
        self.parts = parts
        self.received_messages: list[list[dict[str, str]]] = []

    async def astream(self, state, **kwargs):
        self.received_messages.append(list(state["messages"]))
        for part in self.parts:
            yield part


def message_part(text: str, node: str = "model") -> dict:
    return {
        "type": "messages",
        "data": (FakeToken(text), {"langgraph_node": node}),
    }


async def collect(agent, messages, callback):
    return [chunk async for chunk in stream_agent_text(agent, messages, callback)]


class ChatTests(unittest.TestCase):
    def test_stream_is_progressive_and_hides_tool_output(self):
        agent = FakeAgent(
            [
                message_part("Os pods "),
                message_part("resultado bruto secreto", node="tools"),
                {"type": "updates", "data": {"tools": "não renderizar"}},
                message_part("estão estáveis."),
            ]
        )
        callback = DidacticObservabilityCallback()

        with redirect_stderr(StringIO()):
            callback.question_received("Como estão os pods?")
            chunks = asyncio.run(
                collect(agent, [{"role": "user", "content": "Como estão os pods?"}], callback)
            )

        self.assertEqual(chunks, ["Os pods ", "estão estáveis."])
        self.assertNotIn("secreto", "".join(chunks))

    def test_complete_history_is_resent_on_follow_up(self):
        history = [
            {"role": "user", "content": "Liste os pods."},
            {"role": "assistant", "content": "Há três pods."},
            {"role": "user", "content": "Quais reiniciaram?"},
        ]
        agent = FakeAgent([message_part("Nenhum.")])
        callback = DidacticObservabilityCallback()

        with redirect_stderr(StringIO()):
            callback.question_received(history[-1]["content"])
            chunks = asyncio.run(collect(agent, history, callback))

        self.assertEqual(chunks, ["Nenhum."])
        self.assertEqual(agent.received_messages, [history])

    def test_tool_events_are_sanitized_in_stderr(self):
        callback = DidacticObservabilityCallback()
        run_id = uuid4()
        stderr = StringIO()

        async def emit_events():
            await callback.on_tool_start(
                {"name": "kubectl_get"},
                "",
                run_id=run_id,
                inputs={
                    "resourceType": "pods",
                    "namespace": "kube-system",
                    "token": "valor-secreto",
                    "selector": "app=privado",
                },
            )
            await callback.on_tool_end("conteúdo sensível", run_id=run_id)

        with redirect_stderr(stderr):
            asyncio.run(emit_events())

        output = stderr.getvalue()
        self.assertIn("kubectl_get", output)
        self.assertIn("kube-system", output)
        self.assertIn("[REDACTED]", output)
        self.assertNotIn("valor-secreto", output)
        self.assertNotIn("app=privado", output)
        self.assertNotIn("conteúdo sensível", output)

    def test_non_message_parts_have_no_ui_text(self):
        self.assertEqual(text_from_stream_part({"type": "updates", "data": {}}), "")


if __name__ == "__main__":
    unittest.main()
