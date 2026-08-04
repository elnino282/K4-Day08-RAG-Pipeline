"""Citation rendering for assistant messages."""

from __future__ import annotations

import streamlit as st

from src.ui.constants import SOURCE_LABEL


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(f"{SOURCE_LABEL} ({len(sources)})", expanded=False):
        for source in sources:
            score = source.get("score")
            score_text = f" · {score:.3f}" if isinstance(score, (int, float)) else ""
            st.markdown(f'<div class="source-card"><strong>{source.get("name", "Tài liệu")}</strong><span>{source.get("type", "Tài liệu")}{score_text}</span></div>', unsafe_allow_html=True)
            content = source.get("content", "").strip()
            if content:
                st.caption(f"{content[:280]}{'…' if len(content) > 280 else ''}")
