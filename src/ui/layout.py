"""App shell helpers and stylesheet loading."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.ui.constants import APP_SUBTITLE, APP_TITLE

STYLE_DIR = Path(__file__).parent / "styles"
STYLE_FILES = ("main.css", "sidebar.css", "chat.css", "composer.css", "responsive.css")


def load_css() -> None:
    css = "\n".join(
        (STYLE_DIR / filename).read_text(encoding="utf-8")
        for filename in STYLE_FILES
    )
    font_import = (
        "@import url('https://fonts.googleapis.com/css2?"
        "family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');"
    )
    style_block = f"<style>\n{font_import}\n{css}\n</style>"

    # st.html xử lý CSS-only block ổn định và không render nội dung CSS thành chữ.
    # Giữ fallback để repo vẫn chạy được với các bản Streamlit cũ chưa có st.html.
    if hasattr(st, "html"):
        st.html(style_block)
    else:
        st.markdown(style_block, unsafe_allow_html=True)


def render_main_container():
    st.markdown(f'<header class="app-header"><div><p class="eyebrow">⚡ TRỢ LÝ HỖ TRỢ TRỰC TUYẾN</p><h2>{APP_TITLE}</h2></div><span>{APP_SUBTITLE}</span></header>', unsafe_allow_html=True)
    return st.container()

