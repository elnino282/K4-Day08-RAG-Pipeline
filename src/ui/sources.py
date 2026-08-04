"""Citation rendering for assistant messages."""

from __future__ import annotations

from html import escape

import streamlit as st

from src.ui.constants import SOURCE_LABEL


def _format_badge(score: float | int | None) -> str:
    if not isinstance(score, (int, float)):
        return ""
    # If score is 0.0 - 1.0, format as percentage
    if 0.0 <= score <= 1.0:
        pct = int(round(score * 100))
        badge_cls = "badge-high" if pct >= 75 else ("badge-mid" if pct >= 50 else "badge-low")
        return f'<span class="source-badge {badge_cls}">🎯 {pct}% phù hợp</span>'
    return f'<span class="source-badge badge-mid">★ {score:.3f}</span>'


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(f"📚 {SOURCE_LABEL} ({len(sources)})", expanded=False):
        for index, source in enumerate(sources, start=1):
            score = source.get("score")
            badge_html = _format_badge(score)
            citation_index = source.get("citation_index") or index
            name = escape(str(source.get("name", "Tài liệu không tên")))
            doc_type = escape(str(source.get("type", "Chính sách")))
            content = source.get("content", "").strip()

            st.markdown(
                f'<div class="source-card">'
                f'  <div class="source-header">'
                f'    <strong class="source-name"><span class="citation-number">[{citation_index}]</span> 📄 {name}</strong>'
                f'    <div class="source-meta"><span class="source-type">{doc_type}</span>{badge_html}</div>'
                f'  </div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if content:
                snippet = escape(content[:300] + ("…" if len(content) > 300 else ""))
                st.markdown(f'<blockquote class="source-snippet">{snippet}</blockquote>', unsafe_allow_html=True)

