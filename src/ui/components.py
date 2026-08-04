"""Small reusable Streamlit components."""

from __future__ import annotations

import streamlit as st


def section_label(text: str) -> None:
    st.markdown(f'<p class="section-label">{text}</p>', unsafe_allow_html=True)


def assistant_actions(message_index: int, message_content: str = "") -> None:
    """Interactive copy and feedback action triggers for assistant responses."""
    st.markdown('<div class="assistant-actions-container">', unsafe_allow_html=True)
    c1, c2, c3, _ = st.columns([0.07, 0.07, 0.07, 0.79])
    with c1:
        if st.button("📋", key=f"copy_msg_{message_index}", help="Sao chép câu trả lời"):
            st.toast("Đã lưu nội dung câu trả lời!")
    with c2:
        if st.button("👍", key=f"like_msg_{message_index}", help="Câu trả lời hữu ích"):
            st.toast("Cảm ơn bạn đã ghi nhận! ❤️")
    with c3:
        if st.button("👎", key=f"dislike_msg_{message_index}", help="Cần cải thiện"):
            st.toast("Ghi nhận phản hồi để tiếp tục tối ưu hóa hệ thống.")
    st.markdown("</div>", unsafe_allow_html=True)


def loading_indicator(text: str) -> None:
    st.markdown(f'<div class="loading-indicator"><span></span><span></span><span></span> {text}</div>', unsafe_allow_html=True)

