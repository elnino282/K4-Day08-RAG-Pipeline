"""Integration test for a Streamlit chat submission."""

import unittest

from streamlit.testing.v1 import AppTest


class StreamlitAppTests(unittest.TestCase):
    def test_chat_submission_renders_without_streamlit_exception(self):
        app = AppTest.from_file("app.py")
        app.run(timeout=30)

        app.chat_input[0].set_value("Payment methods?").run(timeout=30)

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.session_state["messages"]), 2)

        app.run(timeout=30)

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.session_state["messages"]), 2)
