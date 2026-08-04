"""Behavior tests for multi-turn conversation memory in Task 10."""

import unittest
from unittest.mock import patch

from src.task10_generation import (
    MAX_HISTORY_CHARS,
    MAX_HISTORY_MESSAGES,
    _condense_query,
    _history_to_contents,
    normalize_history,
)


class NormalizeHistoryTests(unittest.TestCase):
    def test_drops_empty_and_unknown_roles(self):
        history = [
            {"role": "system", "content": "ignored"},
            {"role": "user", "content": "   "},
            {"role": "user", "content": "Payment methods?"},
            {"role": "assistant", "content": "Cards."},
            "not a dict",
        ]

        self.assertEqual(
            normalize_history(history),
            [{"role": "user", "content": "Payment methods?"}, {"role": "assistant", "content": "Cards."}],
        )

    def test_accepts_gemini_model_role_as_assistant(self):
        history = [{"role": "user", "content": "Q"}, {"role": "model", "content": "A"}]

        self.assertEqual(normalize_history(history)[1]["role"], "assistant")

    def test_truncates_long_messages(self):
        history = [{"role": "user", "content": "x" * (MAX_HISTORY_CHARS + 500)}]

        self.assertEqual(len(normalize_history(history)[0]["content"]), MAX_HISTORY_CHARS)

    def test_keeps_recent_messages_and_starts_on_a_user_turn(self):
        history = [
            {"role": "user" if index % 2 == 0 else "assistant", "content": f"m{index}"}
            for index in range(MAX_HISTORY_MESSAGES + 3)
        ]

        normalized = normalize_history(history)

        self.assertLessEqual(len(normalized), MAX_HISTORY_MESSAGES)
        self.assertEqual(normalized[0]["role"], "user")

    def test_non_list_history_is_ignored(self):
        self.assertEqual(normalize_history(None), [])
        self.assertEqual(normalize_history("history"), [])


class HistoryToContentsTests(unittest.TestCase):
    def test_maps_assistant_to_gemini_model_role(self):
        contents = _history_to_contents(
            [{"role": "user", "content": "Q"}, {"role": "assistant", "content": "A"}]
        )

        self.assertEqual(
            contents,
            [
                {"role": "user", "parts": [{"text": "Q"}]},
                {"role": "model", "parts": [{"text": "A"}]},
            ],
        )


class CondenseQueryTests(unittest.TestCase):
    HISTORY = [{"role": "user", "content": "Chính sách hoàn tiền?"}, {"role": "assistant", "content": "..."}]

    def test_without_history_the_query_is_returned_untouched(self):
        with patch("src.task10_generation._call_gemini") as call:
            self.assertEqual(_condense_query("Còn người bán thì sao?", []), "Còn người bán thì sao?")
        call.assert_not_called()

    def test_rewritten_question_is_used_for_retrieval(self):
        with patch("src.task10_generation._call_gemini", return_value="Chính sách hoàn tiền với người bán là gì?"):
            self.assertEqual(
                _condense_query("Còn người bán thì sao?", self.HISTORY),
                "Chính sách hoàn tiền với người bán là gì?",
            )

    def test_multiline_or_quoted_output_is_reduced_to_one_question(self):
        with patch("src.task10_generation._call_gemini", return_value='"Câu hỏi độc lập?"\nGiải thích thừa'):
            self.assertEqual(_condense_query("Còn người bán?", self.HISTORY), "Câu hỏi độc lập?")

    def test_falls_back_to_the_original_query_when_the_model_fails(self):
        with patch("src.task10_generation._call_gemini", side_effect=RuntimeError("quota")):
            self.assertEqual(_condense_query("Còn người bán?", self.HISTORY), "Còn người bán?")

    def test_falls_back_to_the_original_query_on_empty_output(self):
        with patch("src.task10_generation._call_gemini", return_value="   "):
            self.assertEqual(_condense_query("Còn người bán?", self.HISTORY), "Còn người bán?")


if __name__ == "__main__":
    unittest.main()
