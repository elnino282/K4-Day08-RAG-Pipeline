"""Welcome state and chat transcript rendering."""

from __future__ import annotations

import streamlit as st

from src.ui.components import assistant_actions
from src.ui.constants import EMPTY_DESCRIPTION, EMPTY_TITLE, ERROR_TITLE, PROMPT_CARDS, SUGGESTIONS
from src.ui.sources import render_sources
from src.ui.state import set_pending_query


def render_welcome_state() -> None:
    st.markdown(
        f'<section class="welcome-state">'
        f'<p class="eyebrow">✨ E-COMMERCE RAG ASSISTANT</p>'
        f'<h1>{EMPTY_TITLE}</h1>'
        f'<p>{EMPTY_DESCRIPTION}</p>'
        f'</section>',
        unsafe_allow_html=True,
    )
    if PROMPT_CARDS:
        columns = st.columns(2, gap="small")
        for index, card in enumerate(PROMPT_CARDS):
            with columns[index % 2]:
                btn_label = f"{card['icon']}  {card['title']}\n\n{card['query']}"
                if st.button(btn_label, key=f"prompt_card_{index}", use_container_width=True):
                    set_pending_query(st.session_state, card["query"])
                    st.rerun()
    else:
        columns = st.columns(2, gap="small")
        for index, suggestion in enumerate(SUGGESTIONS):
            with columns[index % 2]:
                if st.button(suggestion, key=f"suggestion_{index}", use_container_width=True):
                    set_pending_query(st.session_state, suggestion)
                    st.rerun()



def render_messages(messages: list[dict]) -> None:
    if not messages:
        render_welcome_state()
        return
    for index, message in enumerate(messages):
        role = message.get("role", "assistant")
        with st.chat_message(role, avatar="🤖" if role == "assistant" else None):
            if message.get("error"):
                st.error(f"{ERROR_TITLE}: {message['content']}")
            else:
                st.markdown(message.get("content", ""))
            if role == "assistant":
                render_sources(message.get("sources", []))
                assistant_actions(index)
