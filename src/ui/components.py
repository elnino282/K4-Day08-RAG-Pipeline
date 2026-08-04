"""Small reusable Streamlit components."""

from __future__ import annotations

import streamlit as st


def section_label(text: str) -> None:
    st.markdown(f'<p class="section-label">{text}</p>', unsafe_allow_html=True)


def assistant_actions(message_index: int) -> None:
    """Visual-only placeholders; no clipboard or feedback side effects."""
    st.markdown(
        f'<div class="assistant-actions" aria-label="Actions for message {message_index}">'
        '<span title="Copy (coming soon)">⧉</span><span title="Like (coming soon)">♡</span><span title="Dislike (coming soon)">♧</span></div>',
        unsafe_allow_html=True,
    )


def loading_indicator(text: str) -> None:
    st.markdown(f'<div class="loading-indicator"><span></span>{text}</div>', unsafe_allow_html=True)
