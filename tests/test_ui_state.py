"""Behavior tests for the Streamlit UI conversation state."""

import unittest

from src.ui.state import (
    claim_query,
    clear_all_conversations,
    complete_query,
    delete_conversation,
    get_active_conversation,
    initialize_state,
    set_top_k,
    start_new_conversation,
)


class ConversationStateTests(unittest.TestCase):
    def test_initialize_state_creates_one_active_conversation_and_messages_view(self):
        state = {}

        initialize_state(state)

        self.assertEqual(len(state["conversations"]), 1)
        conversation = get_active_conversation(state)
        self.assertEqual(conversation["messages"], [])
        self.assertIs(state["messages"], conversation["messages"])
        self.assertFalse(state["is_loading"])
        self.assertEqual(state["top_k"], 5)

    def test_claimed_query_is_added_once_and_completed_in_the_active_conversation(self):
        state = {}
        initialize_state(state)

        token = claim_query(state, "What is the return policy?")
        duplicate_token = claim_query(state, "What is the return policy?")

        self.assertIsNotNone(token)
        self.assertIsNone(duplicate_token)
        self.assertEqual(get_active_conversation(state)["messages"], [{"role": "user", "content": "What is the return policy?"}])

        self.assertTrue(complete_query(state, token, answer="Returns are accepted.", sources=[]))
        self.assertEqual(get_active_conversation(state)["messages"][-1], {"role": "assistant", "content": "Returns are accepted.", "sources": []})
        self.assertFalse(state["is_loading"])

    def test_new_conversation_preserves_prior_messages_and_switches_canonical_view(self):
        state = {}
        initialize_state(state)
        first_id = state["active_conversation"]
        token = claim_query(state, "Payment methods?")
        complete_query(state, token, answer="Cards.", sources=[])

        start_new_conversation(state)

        self.assertNotEqual(state["active_conversation"], first_id)
        self.assertEqual(len(state["conversations"]), 2)
        self.assertEqual(state["messages"], [])
        self.assertEqual(next(item for item in state["conversations"] if item["id"] == first_id)["messages"][0]["content"], "Payment methods?")

    def test_delete_and_clear_conversations(self):
        state = {}
        initialize_state(state)
        first_id = state["active_conversation"]
        start_new_conversation(state)
        second_id = state["active_conversation"]

        self.assertEqual(len(state["conversations"]), 2)
        self.assertTrue(delete_conversation(state, second_id))
        self.assertEqual(len(state["conversations"]), 1)
        self.assertEqual(state["active_conversation"], first_id)

        clear_all_conversations(state)
        self.assertEqual(len(state["conversations"]), 1)
        self.assertEqual(state["messages"], [])

    def test_set_top_k_bounds(self):
        state = {}
        initialize_state(state)
        set_top_k(state, 8)
        self.assertEqual(state["top_k"], 8)
        set_top_k(state, 15)  # Out of bounds, ignored
        self.assertEqual(state["top_k"], 8)

