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

    def test_adapter_returns_safe_error_shape_for_malformed_or_failed_rag_response(self):
        malformed = run_rag_query("question", generate_fn=lambda query, top_k: None)
        failed = run_rag_query("question", generate_fn=lambda query, top_k: (_ for _ in ()).throw(RuntimeError("offline")))

        self.assertEqual(malformed, {"answer": "", "sources": [], "error": "RAG returned an invalid response."})
        self.assertEqual(failed, {"answer": "", "sources": [], "error": "offline"})
