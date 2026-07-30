"""
Unit tests for src/agent/memory.py

Tests cover:
- _parse_compaction_response: parsing LLM responses in SUMMARY/FACTS format
- compact_memory: context compaction logic with mocked LLM and DB
"""

from unittest.mock import patch, MagicMock
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
        assert len(facts) == 2
        assert facts[0]["text"] == "User's name is Nell"
        assert facts[1]["text"] == "User enjoys jazz music"

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
        assert len(facts) == 2
        assert facts[0]["text"] == "User likes reading"

    def test_facts_with_structured_actions(self):
        """FACTS with structured actions (ADD, SUPERSEDE, is_pinned)."""
        raw = (
            "SUMMARY: User updated preferences.\n"
            "FACTS: [\n"
            '  {"action": "ADD", "text": "User name is Nell", "is_pinned": true},\n'
            '  {"action": "SUPERSEDE", "old": "User likes React", "text": "User likes Vue", "is_pinned": false}\n'
            "]"
        )
        summary, facts = _parse_compaction_response(raw)
        assert summary == "User updated preferences."
        assert len(facts) == 2
        assert facts[0]["action"] == "ADD"
        assert facts[0]["is_pinned"] is True
        assert facts[1]["action"] == "SUPERSEDE"
        assert facts[1]["old"] == "User likes React"

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
        assert summary == "User likes cats."
        assert len(facts) == 1
        assert facts[0]["text"] == "User likes cats"

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
        assert facts == []


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
        assert result == short_history

    def test_compaction_triggers_and_saves_facts(self, sample_history):
        """
        Full compaction flow with mocked LLM and DB.
        Verifies that messages are archived, facts are saved, and
        the history is replaced with summary + recent messages.
        """
        mock_raw_response = (
            "SUMMARY: User sent test messages and got responses.\n"
            'FACTS: [{"action": "ADD", "text": "User was testing the assistant"}, {"action": "ADD", "text": "User sent 15 messages"}]'
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

            mock_db.get_all_fact_texts.return_value = []
            mock_db.fact_exists.return_value = False
            mock_db.load_pinned_memory.return_value = []
            mock_db.load_relevant_memory.return_value = []
            mock_db.count_memory.return_value = 0
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

            assert mock_db.archive_messages.called, "archive_messages should be called"
            assert mock_db.save_memory_fact.call_count == 2, "Two new facts should be saved"
            mock_db.update_compaction_state.assert_called_once()

            assert len(result) == 4  # 1 system (with summary) + 3 recent messages
            assert result[0]["role"] == "system"
            assert "[Previous Context Summary]: User sent test messages" in result[0]["content"]

    def test_compaction_deduplicates_facts(self, sample_history):
        """Facts that already exist in DB are skipped (not saved again)."""
        mock_raw_response = (
            "SUMMARY: User testing.\n"
            'FACTS: [{"action": "ADD", "text": "User likes testing"}, {"action": "ADD", "text": "User is persistent"}]'
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

            mock_db.get_all_fact_texts.return_value = ["User likes testing"]
            mock_db.load_pinned_memory.return_value = []
            mock_db.load_relevant_memory.return_value = []
            mock_db.fact_exists.side_effect = lambda f: f == "User likes testing"
            mock_db.get_compaction_state.return_value = (0, "")

            compact_memory(
                conversation_history=sample_history,
                max_active_messages=5,
                keep_recent=3,
                model_name="test-model",
                system_prompt="You are a helpful assistant.",
                session_id="test-session",
            )

            assert mock_db.save_memory_fact.call_count == 1
            mock_db.save_memory_fact.assert_called_with("User is persistent", "test-session", is_pinned=False)

    def test_compaction_handles_supersede_action(self, sample_history):
        """Compaction handles SUPERSEDE action by archiving old fact first."""
        mock_raw_response = (
            "SUMMARY: Preference change.\n"
            'FACTS: [{"action": "SUPERSEDE", "old": "User likes React", "text": "User likes Vue", "is_pinned": false}]'
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

            mock_db.get_all_fact_texts.return_value = ["User likes React"]
            mock_db.load_pinned_memory.return_value = []
            mock_db.load_relevant_memory.return_value = []
            mock_db.get_compaction_state.return_value = (0, "")

            compact_memory(
                conversation_history=sample_history,
                max_active_messages=5,
                keep_recent=3,
                model_name="test-model",
                system_prompt="You are a helpful assistant.",
                session_id="test-session",
            )

            mock_db.delete_fact_by_text.assert_called_once_with("User likes React", replaced_by_text="User likes Vue")
            mock_db.save_memory_fact.assert_called_once_with("User likes Vue", "test-session", is_pinned=False)

    def test_compaction_failure_falls_back_to_sliding_window(self, sample_history):
        """When LLM call fails, fall back to returning just recent messages."""
        with (
            patch("src.agent.memory.OpenRouter") as mock_openrouter,
            patch("src.agent.memory.db") as mock_db,
        ):
            mock_client = MagicMock()
            mock_openrouter.return_value.__enter__.return_value = mock_client
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

            assert len(result) == 3
            assert result[0]["content"] == "Response 13"

    def test_compaction_passes_session_id_to_load_relevant_memory(self, sample_history):
        """Compaction passes session_id to load_relevant_memory to isolate session memory."""
        mock_raw_response = (
            "SUMMARY: Session 42 chat.\n"
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
            mock_db.load_pinned_memory.return_value = []
            mock_db.load_relevant_memory.return_value = []

            compact_memory(
                conversation_history=sample_history,
                max_active_messages=5,
                keep_recent=3,
                model_name="test-model",
                system_prompt="You are a helpful assistant.",
                session_id=42,
            )

            mock_db.load_relevant_memory.assert_called_once_with("Response 14", session_id=42)

    def test_prompt_caching_system_message_structure(self):
        """Test build_system_message orders static blocks first and supports cache_control."""
        from src.agent.prompts import build_system_message

        with patch("src.agent.prompts.db") as mock_db, patch("src.agent.prompts.skills_loader") as mock_skills:
            mock_skills.load_readme.return_value = "Test README content"
            mock_skills.build_skills_prompt_block.return_value = "\nAVAILABLE SKILLS:\n- test_skill"
            mock_db.load_pinned_memory.return_value = ["User name is Arm"]

            # Test string version (static-first ordering)
            msg_str = build_system_message(
                invoked_skill_prompt="[Invoked Skill Instructions: test]",
                previous_summary="User asked for help",
                relevant_facts=["User uses Python"],
                use_cache_control=False
            )
            content = msg_str["content"]
            assert "You are an intelligent" in content
            assert content.find("PROJECT README:") < content.find("[Core Memory / Pinned Facts]:")
            assert content.find("[Core Memory / Pinned Facts]:") < content.find("[Invoked Skill Instructions: test]")
            assert content.find("[Invoked Skill Instructions: test]") < content.find("[Previous Context Summary]:")
            assert content.find("[Previous Context Summary]:") < content.find("[Relevant Dynamic Facts]:")

            # Test structured cache_control version for Anthropic/Claude
            msg_cache = build_system_message(
                invoked_skill_prompt="[Invoked Skill Instructions: test]",
                previous_summary="User asked for help",
                relevant_facts=["User uses Python"],
                use_cache_control=True
            )
            blocks = msg_cache["content"]
            assert isinstance(blocks, list)
            assert len(blocks) == 2
            assert "cache_control" in blocks[0]
            assert blocks[0]["cache_control"] == {"type": "ephemeral"}


if __name__ == "__main__":
    import sys
    print("\n🚀 Running tests/test_memory.py with pytest runner...\n")
    sys.exit(pytest.main(["-v", __file__]))