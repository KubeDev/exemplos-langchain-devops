import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import AsyncMock, patch

from src.app import compor_solicitacao, main


class CliTest(unittest.TestCase):
    def test_namespace_e_contexto_da_solicitacao(self) -> None:
        self.assertEqual(
            compor_solicitacao("Liste os pods", "kube-system"),
            "Liste os pods\nContexto adicional: namespace Kubernetes kube-system.",
        )

    def test_pergunta_sem_namespace_permanece_inalterada(self) -> None:
        self.assertEqual(compor_solicitacao("Liste os pods", None), "Liste os pods")

    @patch("src.app.executar", new_callable=AsyncMock, return_value="pod-a: Running")
    def test_sucesso_imprime_somente_resposta_no_stdout(self, executar: AsyncMock) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            main(["Liste os pods", "--namespace", "kube-system"])

        self.assertEqual(stdout.getvalue(), "pod-a: Running\n")
        self.assertEqual(stderr.getvalue(), "")
        executar.assert_awaited_once_with("Liste os pods", "kube-system")

    @patch("src.app.executar", new_callable=AsyncMock, side_effect=RuntimeError("falha MCP"))
    def test_falha_de_execucao_retorna_codigo_um(self, executar: AsyncMock) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with self.assertRaises(SystemExit) as exit_info:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                main(["Liste os pods"])

        self.assertEqual(exit_info.exception.code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(
            stderr.getvalue(), "Falha durante a execução: RuntimeError\n"
        )

    @patch(
        "src.app.executar",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Authorization: Bearer segredo-demo"),
    )
    def test_falha_nao_expoe_mensagem_da_excecao(self, executar: AsyncMock) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with self.assertRaises(SystemExit) as exit_info:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                main(["Liste os pods"])

        self.assertEqual(exit_info.exception.code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(
            stderr.getvalue(), "Falha durante a execução: RuntimeError\n"
        )
        self.assertNotIn("segredo-demo", stderr.getvalue())

    def test_pergunta_ausente_retorna_codigo_dois(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with self.assertRaises(SystemExit) as exit_info:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                main([])

        self.assertEqual(exit_info.exception.code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("the following arguments are required: pergunta", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
