import asyncio
from uuid import uuid4

from src.observability import DidacticObservabilityCallback, MAX_SUMMARY_LENGTH


def test_tool_event_sanitizes_arguments_and_applies_allowlists(capsys) -> None:
    callback = DidacticObservabilityCallback()
    secret = "segredo-que-nao-pode-aparecer"
    unsafe_value = "namespace-fora-do-cenario"

    asyncio.run(
        callback.on_tool_start(
            {"name": "ferramenta_desconhecida"},
            "entrada-ignorada",
            run_id=uuid4(),
            inputs={
                "resourceType": "pods",
                "namespace": "kube-system",
                "name": unsafe_value,
                "authorization": secret,
                "api-key": secret,
                "password": secret,
                "secret": secret,
                "token": secret,
            },
        )
    )

    stderr = capsys.readouterr().err
    assert "ferramenta iniciada: <nome omitido>" in stderr
    assert '"resourceType": "pods"' in stderr
    assert '"namespace": "kube-system"' in stderr
    assert stderr.count("[REDACTED]") == 5
    assert secret not in stderr
    assert unsafe_value not in stderr
    assert "<texto omitido>" in stderr


def test_tool_argument_summary_has_structural_limit(capsys) -> None:
    callback = DidacticObservabilityCallback()
    arguments = {f"campo_{index}": "valor privado" for index in range(30)}

    asyncio.run(
        callback.on_tool_start(
            {"name": "kubectl_get"},
            "entrada-ignorada",
            run_id=uuid4(),
            inputs=arguments,
        )
    )

    stderr = capsys.readouterr().err.rstrip("\n")
    summary = stderr.split("; argumentos: ", maxsplit=1)[1]
    assert summary.endswith("…")
    assert len(summary.removesuffix("…")) == MAX_SUMMARY_LENGTH
    assert "valor privado" not in stderr


def test_question_answer_and_tool_result_are_logged_without_content(capsys) -> None:
    callback = DidacticObservabilityCallback()
    question = "conteudo confidencial da pergunta"
    answer = "conteudo confidencial da resposta"
    tool_output = "conteudo confidencial retornado pela ferramenta"
    run_id = uuid4()

    callback.question_received(question)
    asyncio.run(
        callback.on_tool_start(
            {"name": "kubectl_get"},
            "entrada-ignorada",
            run_id=run_id,
            inputs={"resourceType": "pods"},
        )
    )
    asyncio.run(callback.on_tool_end(tool_output, run_id=run_id))
    callback.final_answer(answer)

    stderr = capsys.readouterr().err
    assert f"pergunta recebida: {len(question)} caracteres" in stderr
    assert f"resultado: texto com {len(tool_output)} caracteres" in stderr
    assert f"resposta final: gerada ({len(answer)} caracteres)" in stderr
    assert question not in stderr
    assert tool_output not in stderr
    assert answer not in stderr
