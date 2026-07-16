"""
Unit tests for src/agent/memory.py

Tests cover:
- _parse_compaction_response: parsing LLM responses in SUMMARY/FACTS format
- compact_memory: context compaction logic with mocked LLM and DB
"""

from unittest.mock import patch, MagicMock, PropertyMock
import json
import pytest

from src.agent.memory import _parse_compaction_response, compact_memory


# =============================================================================
# Tests for _parse_compaction_response
# =============================================================================

class TestParseCompactionResponse:
    """Tests for the low-level response parser."""

    def test_standard_format(self):
        """Standard SUMMARY + FACTS format."""
        raw = (
            "SUMMARY: The user's name is Nell and they enjoy jazz music.\n"
            'FACTS: ["User\'s name is Nell", "User enjoys jazz music"]'
        )
        summary, facts = _parse_compaction_response(raw)
        assert summary == "The user's name is Nell and they enjoy jazz music."
        assert facts == ["User's name is Nell", "User enjoys jazz music"]

    def test_summary_only_no_facts(self):
        """Only SUMMARY, no FACTS section."""
        raw = "SUMMARY: User asked about the weather."
        summary, facts = _parse_compaction_response(raw)
        assert summary == "User asked about the weather."
        assert facts == []

    def test_facts_with_json_codeblock(self):
        """FACTS wrapped in a markdown JSON code block."""
        raw = (
            "SUMMARY: Discussion about hobbies.\n"
            "FACTS: ```json\n"
            '["User likes reading", "User enjoys hiking"]\n'
            "```"
        )
        summary, facts = _parse_compaction_response(raw)
        assert summary == "Discussion about hobbies."
        assert facts == ["User likes reading", "User enjoys hiking"]

    def test_facts_with_plain_codeblock(self):
        """FACTS wrapped in a plain code block (no json marker)."""
        raw = (
            "SUMMARY: Tech talk.\n"
            "FACTS: ```\n"
            '["User uses Python", "User prefers Linux"]\n'
            "```"
        )
        summary, facts = _parse_compaction_response(raw)
        assert summary == "Tech talk."
        assert facts == ["User uses Python", "User prefers Linux"]

    def test_facts_empty_array(self):
        """FACTS with an empty JSON array."""
        raw = "SUMMARY: Small talk.\nFACTS: []"
        summary, facts = _parse_compaction_response(raw)
        assert summary == "Small talk."
        assert facts == []

    def test_no_summary_prefix(self):
        """Response contains FACTS but SUMMARY: prefix is missing."""
        raw = "User likes cats.\nFACTS: [\"User likes cats\"]"
        summary, facts = _parse_compaction_response(raw)
        # The entire text before FACTS becomes the summary
        assert summary == "User likes cats."
        assert facts == ["User likes cats"]

    def test_malformed_facts_not_json(self):
        """FACTS section is not valid JSON – should return empty list."""
        raw = "SUMMARY: Random.\nFACTS: not json at all"
        summary, facts = _parse_compaction_response(raw)
        assert summary == "Random."
        assert facts == []

    def test_malformed_facts_nested_object(self):
        """FACTS contains a JSON object instead of array – should return empty list."""
        raw = (
            "SUMMARY: Preferences.\n"
            'FACTS: {"name": "Nell", "hobby": "jazz"}'
        )
        summary, facts = _parse_compaction_response(raw)
        assert summary == "Preferences."
        # json.loads succeeds but it's a dict, not a list – list comprehension
        # for f in parsed would iterate over dict keys, which is wrong.
        # But the code does: if isinstance(parsed, list) -> only then processes.
        # So this should return [].
        assert facts == []

    def test_empty_facts_stripped(self):
        """Facts list contains empty strings which should be stripped."""
        raw = (
            "SUMMARY: Notes.\n"
            'FACTS: ["Valid fact", "", "  ", "Another fact"]'
        )
        summary, facts = _parse_compaction_response(raw)
        assert summary == "Notes."
        assert facts == ["Valid fact", "Another fact"]

    def test_raw_text_no_markers(self):
        """No SUMMARY or FACTS markers at all."""
        raw = "Just some random text without markers."
        summary, facts = _parse_compaction_response(raw)
        assert summary == "Just some random text without markers."
        assert facts == []

    def test_summary_case_insensitive_check(self):
        """SUMMARY: prefix check is case-insensitive via .upper()."""
        raw = "summary: Lowercase prefix works.\nFACTS: []"
        summary, facts = _parse_compaction_response(raw)
        assert summary == "Lowercase prefix works."
        assert facts == []

    def test_facts_with_extra_whitespace(self):
        """Extra whitespace around FACTS values."""
        raw = (
            "SUMMARY: Hobbies.\n"
            'FACTS: ["  Spaced fact  ", "another"]'
        )
        summary, facts = _parse_compaction_response(raw)
        assert summary == "Hobbies."
        assert facts == ["Spaced fact", "another"]


# =============================================================================
# Tests for compact_memory
# =============================================================================

class TestCompactMemory:
    """Tests for the main memory compaction function."""

    @pytest.fixture
    def sample_history(self):
        """Build a conversation history with enough messages to trigger compaction."""
        history = [
            {"role": "system", "content": "You are a helpful assistant."},
        ]
        for i in range(15):
            history.append({"role": "user", "content": f"Message {i}"})
            history.append({"role": "assistant", "content": f"Response {i}"})
        return history

    @pytest.fixture
    def short_history(self):
        """Build a history below the compaction threshold."""
        return [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]

    def test_below_threshold_no_compaction(self, short_history):
        """History is shorter than max_active_messages – no compaction."""
        result = compact_memory(
            conversation_history=short_history,
            max_active_messages=50,
            keep_recent=5,
            model_name="test-model",
            system_prompt="You are a helpful assistant.",
            session_id="test-session",
        )
        # Should return the same history unchanged
        assert result == short_history

    def test_compaction_triggers_and_saves_facts(self, sample_history):
        """
        Full compaction flow with mocked LLM and DB.
        Verifies that messages are archived, facts are saved, and
        the history is replaced with summary + recent messages.
        """
        mock_raw_response = (
            "SUMMARY: User sent test messages and got responses.\n"
            'FACTS: ["User was testing the assistant", "User sent 15 messages"]'
        )

        with (
            patch("src.agent.memory.OpenRouter") as mock_openrouter,
            patch("src.agent.memory.db") as mock_db,
        ):
            # Mock the OpenRouter context manager and chat response
            mock_client = MagicMock()
            mock_openrouter.return_value.__enter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.choices[0].message.content = mock_raw_response
            mock_client.chat.send.return_value = mock_response

            # Mock DB calls
            mock_db.fact_exists.return_value = False
            mock_db.get_compaction_state.return_value = (0, "")
            mock_db.archive_messages.return_value = None

            result = compact_memory(
                conversation_history=sample_history,
                max_active_messages=5,
                keep_recent=3,
                model_name="test-model",
                system_prompt="You are a helpful assistant.",
                session_id="test-session",
            )

            # Verify DB interactions
            assert mock_db.archive_messages.called, "archive_messages should be called"
            assert mock_db.save_memory_fact.call_count == 2, "Two new facts should be saved"
            mock_db.update_compaction_state.assert_called_once()

            # Verify result structure
            assert len(result) == 4  # 1 system (with summary) + 3 recent messages
            assert result[0]["role"] == "system"
            assert "[Previous Context Summary]: User sent test messages" in result[0]["content"]
            # sample_history[-3:] = indices 28,29,30 = Response 13, Message 14, Response 14
            assert result[1]["content"] == "Response 13"

    def test_compaction_deduplicates_facts(self, sample_history):
        """Facts that already exist in DB are skipped (not saved again)."""
        mock_raw_response = (
            "SUMMARY: User testing.\n"
            'FACTS: ["User likes testing", "User is persistent"]'
        )

        with (
            patch("src.agent.memory.OpenRouter") as mock_openrouter,
            patch("src.agent.memory.db") as mock_db,
        ):
            mock_client = MagicMock()
            mock_openrouter.return_value.__enter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.choices[0].message.content = mock_raw_response
            mock_client.chat.send.return_value = mock_response

            # First fact exists, second doesn't
            mock_db.fact_exists.side_effect = lambda f: f == "User likes testing"
            mock_db.get_compaction_state.return_value = (0, "")

            result = compact_memory(
                conversation_history=sample_history,
                max_active_messages=5,
                keep_recent=3,
                model_name="test-model",
                system_prompt="You are a helpful assistant.",
                session_id="test-session",
            )

            # Only 1 new fact should be saved (the second one)
            assert mock_db.save_memory_fact.call_count == 1
            mock_db.save_memory_fact.assert_called_with("User is persistent", "test-session")

    def test_compaction_failure_falls_back_to_sliding_window(self, sample_history):
        """When LLM call fails, fall back to returning just recent messages."""
        with (
            patch("src.agent.memory.OpenRouter") as mock_openrouter,
            patch("src.agent.memory.db") as mock_db,
        ):
            mock_client = MagicMock()
            mock_openrouter.return_value.__enter__.return_value = mock_client
            # Raise an exception when chat.send is called
            mock_client.chat.send.side_effect = Exception("API error")
            mock_db.get_compaction_state.return_value = (0, "")

            result = compact_memory(
                conversation_history=sample_history,
                max_active_messages=5,
                keep_recent=3,
                model_name="test-model",
                system_prompt="You are a helpful assistant.",
                session_id="test-session",
            )

            # Fallback: just recent messages (no system summary)
            # recent_messages = history[-3:] = [Response 13, Message 14, Response 14]
            assert len(result) == 3
            assert result[0]["content"] == "Response 13"

    def test_compaction_skips_system_message_in_archived_count(self, sample_history):
        """
        The synthetic system prompt at index 0 should not be counted
        in the archived message watermark.
        """
        mock_raw_response = (
            "SUMMARY: Testing.\n"
            "FACTS: []"
        )

        with (
            patch("src.agent.memory.OpenRouter") as mock_openrouter,
            patch("src.agent.memory.db") as mock_db,
        ):
            mock_client = MagicMock()
            mock_openrouter.return_value.__enter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.choices[0].message.content = mock_raw_response
            mock_client.chat.send.return_value = mock_response

            mock_db.fact_exists.return_value = False
            mock_db.get_compaction_state.return_value = (0, "")

            # history has 1 system + 15 user + 15 assistant = 31 messages
            # max_active_messages=5, keep_recent=3
            # messages_to_compact = 31 - 3 = 28 messages
            # Among those 28, the first one is "system" role - should not be counted
            # newly_archived_count should be 27 (28 - 1 system)
            compact_memory(
                conversation_history=sample_history,
                max_active_messages=5,
                keep_recent=3,
                model_name="test-model",
                system_prompt="You are a helpful assistant.",
                session_id="test-session",
            )

            # verify update_compaction_state was called with correct count
            # prev_archived_count (0) + newly_archived_count (27)
            call_args = mock_db.update_compaction_state.call_args
            assert call_args is not None
            args, kwargs = call_args
            assert args[1] == 27, (
                f"Expected archived count 27 (28 compacted - 1 system), "
                f"got {args[1]}"
            )

    def test_compaction_updates_system_prompt_with_summary(self, sample_history):
        """The system prompt should be updated with the compaction summary."""
        mock_raw_response = (
            "SUMMARY: User tested message handling.\n"
            "FACTS: []"
        )

        with (
            patch("src.agent.memory.OpenRouter") as mock_openrouter,
            patch("src.agent.memory.db") as mock_db,
        ):
            mock_client = MagicMock()
            mock_openrouter.return_value.__enter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.choices[0].message.content = mock_raw_response
            mock_client.chat.send.return_value = mock_response

            mock_db.fact_exists.return_value = False
            mock_db.get_compaction_state.return_value = (0, "")

            result = compact_memory(
                conversation_history=sample_history,
                max_active_messages=5,
                keep_recent=3,
                model_name="test-model",
                system_prompt="You are a helpful assistant.",
                session_id="test-session",
            )

            # System prompt should contain the original + summary
            expected_content = (
                "You are a helpful assistant.\n\n"
                "[Previous Context Summary]: User tested message handling."
            )
            assert result[0]["content"] == expected_content

    def test_compaction_no_facts_extracted(self, sample_history):
        """When no facts are extracted, no save_memory_fact calls should occur."""
        mock_raw_response = (
            "SUMMARY: General chat.\n"
            "FACTS: []"
        )

        with (
            patch("src.agent.memory.OpenRouter") as mock_openrouter,
            patch("src.agent.memory.db") as mock_db,
        ):
            mock_client = MagicMock()
            mock_openrouter.return_value.__enter__.return_value = mock_client
            mock_response = MagicMock()
            mock_response.choices[0].message.content = mock_raw_response
            mock_client.chat.send.return_value = mock_response

            mock_db.get_compaction_state.return_value = (0, "")

            result = compact_memory(
                conversation_history=sample_history,
                max_active_messages=5,
                keep_recent=3,
                model_name="test-model",
                system_prompt="You are a helpful assistant.",
                session_id="test-session",
            )

            mock_db.save_memory_fact.assert_not_called()
            assert result[0]["role"] == "system"
            assert "[Previous Context Summary]: General chat." in result[0]["content"]