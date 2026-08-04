"""Sidebar navigation and session-scoped conversation history."""

from __future__ import annotations

import streamlit as st

from src.ui.components import section_label
from src.ui.constants import APP_SUBTITLE, APP_TITLE, NEW_CONVERSATION_LABEL
from src.ui.state import select_conversation, start_new_conversation


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(f'<div class="brand"><span class="brand-mark">◆</span><div><strong>{APP_TITLE}</strong><small>{APP_SUBTITLE}</small></div></div>', unsafe_allow_html=True)
        if st.button(f"＋ {NEW_CONVERSATION_LABEL}", use_container_width=True, key="new_conversation", disabled=st.session_state.is_loading):
            start_new_conversation(st.session_state)
            st.rerun()

        section_label("GẦN ĐÂY")
        for conversation in st.session_state.conversations:
            is_active = conversation["id"] == st.session_state.active_conversation
            label = f"● {conversation['title']}" if is_active else conversation["title"]
            if st.button(label, key=f"conversation_{conversation['id']}", use_container_width=True, disabled=st.session_state.is_loading):
                if select_conversation(st.session_state, conversation["id"]):
                    st.rerun()

        st.markdown('<div class="sidebar-footer"><strong>Phiên làm việc</strong><span>Lịch sử chỉ được lưu trong phiên hiện tại.</span></div>', unsafe_allow_html=True)
