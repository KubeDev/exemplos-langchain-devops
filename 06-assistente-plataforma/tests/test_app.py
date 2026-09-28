import asyncio
import builtins
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

os.environ.setdefault("ANTHROPIC_API_KEY", "chave-ficticia-para-testes")
os.environ.setdefault("KUBERNETES_MCP_TOKEN", "token-ficticio-para-testes")

from src import app


class FakeAdapter:
    def __init__(self, config) -> None:
        self.config = config
        self.tools = [SimpleNamespace(name="kubectl_get"), SimpleNamespace(name="ping")]

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        return None

    async def list_tools(self):
        return self.tools


class FakeAgent:
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.ainvoke = AsyncMock(
            return_value={"messages": [SimpleNamespace(text=self.answer)]}
        )
        self.stream = Mock(side_effect=AssertionError("streaming não deve ser usado"))
        self.astream = Mock(side_effect=AssertionError("streaming não deve ser usado"))
        self.astream_events = Mock(side_effect=AssertionError("streaming não deve ser usado"))


def test_single_mocked_interaction_uses_ainvoke_without_streaming_and_separates_output(
    monkeypatch, capsys
) -> None:
    question = "listar pods sem expor esta pergunta"
    answer = "resposta visivel somente no stdout"
    fake_agent = FakeAgent(answer)
    input_mock = Mock(side_effect=lambda prompt: print(prompt, end="") or question)

    monkeypatch.setattr(app, "ChatAnthropic", Mock(return_value=object()))
    monkeypatch.setattr(app, "MCPAdapter", FakeAdapter)
    monkeypatch.setattr(app, "create_agent", Mock(return_value=fake_agent))
    monkeypatch.setattr(builtins, "input", input_mock)

    asyncio.run(app.executar())

    captured = capsys.readouterr()
    assert input_mock.call_count == 1
    fake_agent.ainvoke.assert_awaited_once()
    (payload,) = fake_agent.ainvoke.await_args.args
    config = fake_agent.ainvoke.await_args.kwargs["config"]
    assert payload == {"messages": [("human", question)]}
    assert len(config["callbacks"]) == 1
    assert fake_agent.stream.call_count == 0
    assert fake_agent.astream.call_count == 0
    assert fake_agent.astream_events.call_count == 0

    assert "Ferramentas MCP disponíveis:" in captured.out
    assert "- kubectl_get" in captured.out
    assert "- ping" in captured.out
    assert "Pergunta: " in captured.out
    assert "Resposta:" in captured.out
    assert answer in captured.out
    assert "[observabilidade]" not in captured.out

    assert "[observabilidade] pergunta recebida:" in captured.err
    assert "[observabilidade] resposta final: gerada" in captured.err
    assert question not in captured.err
    assert answer not in captured.err
    assert "Ferramentas MCP disponíveis:" not in captured.err
