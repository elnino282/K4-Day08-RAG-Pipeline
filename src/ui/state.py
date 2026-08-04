"""Single-source-of-truth conversation state helpers."""

from __future__ import annotations

from collections.abc import MutableMapping
from uuid import uuid4

from src.ui.constants import DEFAULT_TOP_K, HISTORY_MESSAGE_LIMIT, MAX_TITLE_LENGTH, NEW_CONVERSATION_LABEL


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
    state.setdefault("top_k", DEFAULT_TOP_K)
    _sync_messages_view(state)



def get_active_conversation(state: MutableMapping) -> dict:
    active_id = state["active_conversation"]
    for conversation in state["conversations"]:
        if conversation["id"] == active_id:
            return conversation
    state["active_conversation"] = state["conversations"][0]["id"]
    return state["conversations"][0]


def get_history(state: MutableMapping, max_messages: int = HISTORY_MESSAGE_LIMIT) -> list[dict]:
    """Return completed exchanges of the active conversation, oldest first.

    Only user/assistant pairs that produced a real answer are kept: a failed turn
    would teach the model that an error message is a valid reply, and the trailing
    user message is the question being answered right now, not history.
    """
    history: list[dict] = []
    pending_question: str | None = None

    for message in get_active_conversation(state)["messages"]:
        role = message.get("role")
        if role == "user":
            pending_question = str(message.get("content") or "")
        elif role == "assistant" and pending_question is not None:
            if not message.get("error"):
                history.append({"role": "user", "content": pending_question})
                history.append({"role": "assistant", "content": str(message.get("content") or "")})
            pending_question = None

    return history[-max_messages:] if max_messages > 0 else []


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


def delete_conversation(state: MutableMapping, conversation_id: str) -> bool:
    if state.get("is_loading"):
        return False
    conversations = state.get("conversations", [])
    index_to_remove = None
    for index, item in enumerate(conversations):
        if item["id"] == conversation_id:
            index_to_remove = index
            break
    if index_to_remove is None:
        return False

    conversations.pop(index_to_remove)
    if not conversations:
        new_conv = _new_conversation()
        state["conversations"] = [new_conv]
        state["active_conversation"] = new_conv["id"]
    elif state.get("active_conversation") == conversation_id:
        state["active_conversation"] = conversations[0]["id"]

    _sync_messages_view(state)
    return True


def clear_all_conversations(state: MutableMapping) -> None:
    if state.get("is_loading"):
        return
    new_conv = _new_conversation()
    state["conversations"] = [new_conv]
    state["active_conversation"] = new_conv["id"]
    state["pending_query"] = None
    _sync_messages_view(state)


def set_top_k(state: MutableMapping, top_k: int) -> None:
    if 1 <= top_k <= 10:
        state["top_k"] = top_k

