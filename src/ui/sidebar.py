"""Sidebar navigation and session-scoped conversation history."""

from __future__ import annotations

import streamlit as st

from src.ui.components import section_label
from src.ui.constants import APP_SUBTITLE, APP_TITLE, DEFAULT_TOP_K, NEW_CONVERSATION_LABEL
from src.ui.state import clear_all_conversations, delete_conversation, select_conversation, set_top_k, start_new_conversation


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(f'<div class="brand"><span class="brand-mark">◆</span><div><strong>{APP_TITLE}</strong><small>{APP_SUBTITLE}</small></div></div>', unsafe_allow_html=True)
        if st.button(f"＋ {NEW_CONVERSATION_LABEL}", use_container_width=True, key="new_conversation", disabled=st.session_state.is_loading):
            start_new_conversation(st.session_state)
            st.rerun()

        section_label("GẦN ĐÂY")
        conversations = st.session_state.get("conversations", [])
        for conversation in conversations:
            is_active = conversation["id"] == st.session_state.active_conversation
            msg_count = len(conversation.get("messages", []))
            count_suffix = f" ({msg_count})" if msg_count > 0 else ""
            label = f"● {conversation['title']}{count_suffix}" if is_active else f"{conversation['title']}{count_suffix}"
            
            col1, col2 = st.columns([0.83, 0.17])
            with col1:
                if st.button(label, key=f"conversation_{conversation['id']}", use_container_width=True, disabled=st.session_state.is_loading):
                    if select_conversation(st.session_state, conversation["id"]):
                        st.rerun()
            with col2:
                if st.button("✕", key=f"delete_{conversation['id']}", help="Xóa hội thoại này", disabled=st.session_state.is_loading):
                    if delete_conversation(st.session_state, conversation["id"]):
                        st.rerun()

        st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)

        with st.expander("⚙️ Cấu hình Tra cứu", expanded=False):
            current_top_k = st.session_state.get("top_k", DEFAULT_TOP_K)
            new_top_k = st.slider("Số tài liệu tra cứu (Top-K)", min_value=1, max_value=10, value=current_top_k, step=1, disabled=st.session_state.is_loading)
            if new_top_k != current_top_k:
                set_top_k(st.session_state, new_top_k)
                st.rerun()

        if len(conversations) > 1 or any(c.get("messages") for c in conversations):
            if st.button("🗑️ Xóa lịch sử", use_container_width=True, key="clear_all_history", disabled=st.session_state.is_loading):
                clear_all_conversations(st.session_state)
                st.toast("Đã làm sạch lịch sử trò chuyện!")
                st.rerun()

        st.markdown('<div class="sidebar-footer"><strong>Phiên làm việc</strong><span>Lịch sử chỉ được lưu trong phiên hiện tại.</span></div>', unsafe_allow_html=True)

