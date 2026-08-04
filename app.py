"""Streamlit entry point for the E-commerce Support RAG interface."""

from pathlib import Path
import sys

import streamlit as st
from dotenv import load_dotenv

from src.ui.chat import render_messages
from src.ui.components import loading_indicator
from src.ui.composer import render_composer
from src.ui.constants import APP_ICON, APP_TITLE, LOADING_TEXT
from src.ui.layout import load_css, render_main_container
from src.ui.rag_adapter import run_rag_query
from src.ui.sidebar import render_sidebar
from src.ui.sources import render_sources
from src.ui.state import (
    claim_query,
    complete_query,
    consume_pending_query,
    get_active_conversation,
    get_history,
    initialize_state,
)

PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide", initial_sidebar_state="expanded")


def main() -> None:
    initialize_state(st.session_state)
    load_css()
    render_sidebar()

    with render_main_container():
        render_messages(get_active_conversation(st.session_state)["messages"])
        submitted_query = render_composer(st.session_state.is_loading)
        pending_query = consume_pending_query(st.session_state)
        query = submitted_query or pending_query
        token = claim_query(st.session_state, query)

        if token:
            with st.chat_message("user"):
                st.markdown(query.strip())
            with st.chat_message("assistant", avatar="🤖"):
                loading_indicator(LOADING_TEXT)
                top_k = st.session_state.get("top_k", 5)
                # claim_query already appended this turn's question, which get_history skips.
                history = get_history(st.session_state)
                result = run_rag_query(query.strip(), top_k=top_k, history=history)
                complete_query(st.session_state, token, **result)
                if result["error"]:
                    st.error(result["error"])
                else:
                    st.markdown(result["answer"])
                    render_sources(result["sources"])
            st.rerun()


if __name__ == "__main__":
    main()
