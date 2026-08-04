"""Normalize the existing RAG response for presentation without changing src/."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.ui.constants import DEFAULT_TOP_K, INVALID_RAG_RESPONSE


def _as_score(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _normalize_source(source: Any) -> dict | None:
    if not isinstance(source, dict):
        return None
    metadata = source.get("metadata") if isinstance(source.get("metadata"), dict) else {}
    return {
        "name": str(metadata.get("source") or source.get("name") or "Tài liệu không rõ tên"),
        "type": str(metadata.get("type") or source.get("type") or "Tài liệu"),
        "score": _as_score(source.get("score")),
        "content": str(source.get("content") or ""),
    }


def run_rag_query(query: str, generate_fn: Callable[..., Any] | None = None, top_k: int = DEFAULT_TOP_K) -> dict:
    """Return the stable UI result shape for any RAG success/failure response."""
    if generate_fn is None:
        from src.task10_generation import generate_with_citation

        generate_fn = generate_with_citation
    try:
        response = generate_fn(query, top_k=top_k)
    except Exception as error:  # The UI must surface pipeline failures safely.
        return {"answer": "", "sources": [], "error": str(error) or "RAG request failed."}

    if not isinstance(response, dict):
        return {"answer": "", "sources": [], "error": INVALID_RAG_RESPONSE}

    answer = response.get("answer")
    if answer is None:
        return {"answer": "", "sources": [], "error": INVALID_RAG_RESPONSE}

    raw_sources = response.get("sources", [])
    sources = [_normalize_source(source) for source in raw_sources] if isinstance(raw_sources, list) else []
    return {"answer": str(answer), "sources": [source for source in sources if source is not None], "error": None}
