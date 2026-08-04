"""App shell helpers and stylesheet loading."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.ui.constants import APP_SUBTITLE, APP_TITLE

STYLE_DIR = Path(__file__).parent / "styles"
STYLE_FILES = ("main.css", "sidebar.css", "chat.css", "composer.css", "responsive.css")


def load_css() -> None:
    css = "\n".join((STYLE_DIR / filename).read_text(encoding="utf-8") for filename in STYLE_FILES)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_main_container():
    st.markdown(f'<header class="app-header"><div><p class="eyebrow">TRỢ LÝ CHÍNH SÁCH</p><h2>{APP_TITLE}</h2></div><span>{APP_SUBTITLE}</span></header>', unsafe_allow_html=True)
    return st.container()
