"""Rounded chat composer using Streamlit's native submit behavior."""

from __future__ import annotations

import streamlit as st

from src.ui.constants import INPUT_PLACEHOLDER


def render_composer(disabled: bool) -> str | None:
    st.markdown('<div class="composer-anchor"></div>', unsafe_allow_html=True)
    return st.chat_input(INPUT_PLACEHOLDER, disabled=disabled)
