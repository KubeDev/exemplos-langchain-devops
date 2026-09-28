import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class AppTests(unittest.TestCase):
    def test_initial_ui_has_only_the_chat_input(self):
        app_path = Path(__file__).resolve().parent.parent / "src" / "app.py"
        app = AppTest.from_file(str(app_path)).run(timeout=10)

        self.assertFalse(app.exception)
        self.assertEqual(len(app.chat_input), 1)
        self.assertEqual(len(app.chat_message), 0)
        self.assertEqual(len(app.title), 0)
        self.assertEqual(len(app.button), 0)


if __name__ == "__main__":
    unittest.main()
