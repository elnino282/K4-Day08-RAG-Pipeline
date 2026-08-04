"""Single-source-of-truth conversation state helpers."""

from __future__ import annotations

from collections.abc import MutableMapping
from uuid import uuid4

from src.ui.constants import MAX_TITLE_LENGTH, NEW_CONVERSATION_LABEL


def _new_conversation() -> dict:
    return {"id": str(uuid4()), "title": NEW_CONVERSATION_LABEL, "messages": []}


def _sync_messages_view(state: MutableMapping) -> None:
    """Expose a derived compatibility view; conversations remain canonical."""
    state["messages"] = get_active_conversation(state)["messages"]


def initialize_state(state: MutableMapping) -> None:
    if "conversations" not in state or not state["conversations"]:
        conversation = _new_conversation()
        state["conversations"] = [conversation]
        state["active_conversation"] = conversation["id"]
    elif "active_conversation" not in state:
        state["active_conversation"] = state["conversations"][0]["id"]

    state.setdefault("pending_query", None)
    state.setdefault("is_loading", False)
    state.setdefault("sidebar_collapsed", False)
    state.setdefault("processing_query_token", None)
    _sync_messages_view(state)


def get_active_conversation(state: MutableMapping) -> dict:
    active_id = state["active_conversation"]
    for conversation in state["conversations"]:
        if conversation["id"] == active_id:
            return conversation
    state["active_conversation"] = state["conversations"][0]["id"]
    return state["conversations"][0]


def _conversation_title(query: str) -> str:
    compact = " ".join(query.split())
    return compact if len(compact) <= MAX_TITLE_LENGTH else f"{compact[: MAX_TITLE_LENGTH - 1]}…"


def start_new_conversation(state: MutableMapping) -> None:
    if state.get("is_loading"):
        return
    conversation = _new_conversation()
    state["conversations"].insert(0, conversation)
    state["active_conversation"] = conversation["id"]
    state["pending_query"] = None
    _sync_messages_view(state)


def select_conversation(state: MutableMapping, conversation_id: str) -> bool:
    if state.get("is_loading") or not any(item["id"] == conversation_id for item in state["conversations"]):
        return False
    state["active_conversation"] = conversation_id
    _sync_messages_view(state)
    return True


def set_pending_query(state: MutableMapping, query: str) -> None:
    if not state.get("is_loading"):
        state["pending_query"] = query


def consume_pending_query(state: MutableMapping) -> str | None:
    query = state.get("pending_query")
    state["pending_query"] = None
    return query


def claim_query(state: MutableMapping, query: str | None) -> str | None:
    cleaned = (query or "").strip()
    if not cleaned or state.get("is_loading"):
        return None

    token = str(uuid4())
    conversation = get_active_conversation(state)
    conversation["messages"].append({"role": "user", "content": cleaned})
    if len(conversation["messages"]) == 1:
        conversation["title"] = _conversation_title(cleaned)
    state["is_loading"] = True
    state["processing_query_token"] = token
    _sync_messages_view(state)
    return token


def complete_query(state: MutableMapping, token: str, *, answer: str, sources: list[dict], error: str | None = None) -> bool:
    if token != state.get("processing_query_token"):
        return False
    conversation = get_active_conversation(state)
    content = answer or error or ""
    message = {"role": "assistant", "content": content, "sources": sources}
    if error:
        message["error"] = error
    conversation["messages"].append(message)
    state["is_loading"] = False
    state["processing_query_token"] = None
    _sync_messages_view(state)
    return True
