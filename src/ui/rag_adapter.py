"""Chuẩn hóa kết quả pipeline Task 10 cho giao diện Streamlit."""

from __future__ import annotations

from collections.abc import Callable
import re
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
    display_score = source.get("jina_score")
    if display_score is None:
        display_score = source.get("dense_score")
    if display_score is None:
        display_score = source.get("score")

    raw_name = str(
            metadata.get("title")
            or metadata.get("source")
            or source.get("name")
            or "Tài liệu không rõ tên"
        )
    display_name = re.sub(
        r"\s*\|\s*Shopee\s+Trung tâm trợ giúp\s*$",
        "",
        raw_name,
        flags=re.IGNORECASE,
    ).strip()

    normalized = {
        "name": display_name or raw_name,
        "type": str(metadata.get("type") or source.get("type") or "Tài liệu"),
        "score": _as_score(display_score),
        "content": str(source.get("content") or ""),
    }
    if source.get("citation_index") is not None:
        normalized["citation_index"] = source["citation_index"]
    return normalized


def run_rag_query(
    query: str,
    generate_fn: Callable[..., Any] | None = None,
    top_k: int = DEFAULT_TOP_K,
    history: list[dict] | None = None,
) -> dict:
    """Return the stable UI result shape for any RAG success/failure response."""
    if generate_fn is None:
        from src.task10_generation import generate_with_citation

        generate_fn = generate_with_citation

    # `history` is only forwarded when there is something to forward, so callers
    # that inject a two-argument generate_fn keep working for first-turn queries.
    call_kwargs: dict = {"top_k": top_k}
    if history:
        call_kwargs["history"] = history

    try:
        response = generate_fn(query, **call_kwargs)
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
