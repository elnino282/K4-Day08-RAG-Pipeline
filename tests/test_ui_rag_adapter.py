"""Contract tests for normalizing RAG output for the UI."""

import unittest

from src.ui.rag_adapter import run_rag_query


class RagAdapterTests(unittest.TestCase):
    def test_adapter_normalizes_answer_and_source_metadata(self):
        result = run_rag_query(
            "question",
            generate_fn=lambda query, top_k: {
                "answer": "A concise answer.",
                "sources": [{"content": "Evidence", "score": "0.875", "metadata": {"source": "policy.md", "type": "legal"}}],
            },
        )

        self.assertEqual(result, {"answer": "A concise answer.", "error": None, "sources": [{"name": "policy.md", "type": "legal", "score": 0.875, "content": "Evidence"}]})

    def test_adapter_passes_top_k_parameter(self):
        passed_top_k = []

        def mock_generate(query, top_k):
            passed_top_k.append(top_k)
            return {"answer": "OK", "sources": []}

        run_rag_query("test", generate_fn=mock_generate, top_k=7)
        self.assertEqual(passed_top_k, [7])

    def test_adapter_forwards_history_when_present(self):
        received = {}

        def mock_generate(query, top_k, history):
            received["history"] = history
            return {"answer": "OK", "sources": []}

        history = [{"role": "user", "content": "Payment methods?"}, {"role": "assistant", "content": "Cards."}]
        run_rag_query("And refunds?", generate_fn=mock_generate, history=history)
        self.assertEqual(received["history"], history)

    def test_adapter_omits_history_argument_when_there_is_none(self):
        def mock_generate(query, top_k):  # Deliberately has no history parameter.
            return {"answer": "OK", "sources": []}

        result = run_rag_query("First question", generate_fn=mock_generate, history=[])
        self.assertEqual(result["error"], None)

