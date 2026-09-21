import unittest

from src.observability import MAX_SUMMARY_LENGTH, _content_summary, _summary


class ObservabilityTest(unittest.TestCase):
    def test_redige_segredos_e_omite_texto_nao_permitido(self) -> None:
        summary = _summary(
            {
                "token": "segredo",
                "namespace": "kube-system",
                "selector": "app=privado",
            }
        )

        self.assertIn("[REDACTED]", summary)
        self.assertIn("kube-system", summary)
        self.assertNotIn("segredo", summary)
        self.assertNotIn("app=privado", summary)

    def test_limita_resumo_serializado(self) -> None:
        summary = _summary({f"campo-{index}": "valor" for index in range(30)})

        self.assertLessEqual(len(summary), MAX_SUMMARY_LENGTH + 1)
        self.assertTrue(summary.endswith("…"))

    def test_resume_resultado_sem_expor_conteudo(self) -> None:
        self.assertEqual(_content_summary("conteúdo sensível"), "texto com 17 caracteres")


if __name__ == "__main__":
    unittest.main()
