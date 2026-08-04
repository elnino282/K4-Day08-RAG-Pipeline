"""App shell helpers and stylesheet loading."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.ui.constants import APP_SUBTITLE, APP_TITLE

STYLE_DIR = Path(__file__).parent / "styles"
STYLE_FILES = ("main.css", "sidebar.css", "chat.css", "composer.css", "responsive.css")


def load_css() -> None:
    font_link = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
    css = "\n".join((STYLE_DIR / filename).read_text(encoding="utf-8") for filename in STYLE_FILES)
    st.html(f"{font_link}\n<style>{css}</style>")


def render_main_container():
    st.markdown(f'<header class="app-header"><div><p class="eyebrow">⚡ TRỢ LÝ HỖ TRỢ TRỰC TUYẾN</p><h2>{APP_TITLE}</h2></div><span>{APP_SUBTITLE}</span></header>', unsafe_allow_html=True)
    return st.container()

