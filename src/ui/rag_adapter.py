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


def _display_score(source: dict) -> float | None:
    """Pick the score a reader can interpret, not the one used for ordering.

    After RRF fusion (Task 7) `score` holds the fused rank score, which peaks near
    1/(k+1) ~= 0.016 no matter how relevant the chunk is — rendered as a percentage
    that reads as "3% phù hợp" for even a perfect match. `rerank_rrf` keeps the
    per-ranker originals, so prefer the dense cosine similarity, which is a real
    [0,1] relevance figure. Fall back to `score` for results that never went
    through fusion (e.g. the PageIndex path).
    """
    dense_score = _as_score(source.get("dense_score"))
    if dense_score is not None:
        return dense_score

    # Chunk chỉ do BM25 tìm ra: `bm25_score` là điểm thô (có thể > 20), không phải
    # thang [0,1], nên hiển thị dưới dạng phần trăm sẽ sai. Bỏ badge thay vì bịa số.
    if source.get("bm25_score") is not None:
        return None

    return _as_score(source.get("score"))


def _normalize_source(source: Any) -> dict | None:
    if not isinstance(source, dict):
        return None
    metadata = source.get("metadata") if isinstance(source.get("metadata"), dict) else {}
    return {
        "name": str(metadata.get("source") or source.get("name") or "Tài liệu không rõ tên"),
        "type": str(metadata.get("type") or source.get("type") or "Tài liệu"),
        "score": _display_score(source),
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
