"""
test_eval_memory.py — Evaluation test suite for memory compaction and context retention.
"""

import pytest
from src.agent import memory

class TestMemoryCompactionEvals:
    def test_parse_compaction_response_structured_format(self):
        """Verifies parsing of SUMMARY and FACTS JSON output."""
        sample_response = (
            "SUMMARY: User is developing an async FastAPI app with PostgreSQL on port 8080.\n"
            "FACTS: [\n"
            '  {"action": "ADD", "text": "App uses FastAPI and asyncpg", "is_pinned": false},\n'
            '  {"action": "ADD", "text": "Main port is 8080", "is_pinned": true}\n'
            "]"
        )
        summary, facts = memory._parse_compaction_response(sample_response)
        assert "FastAPI" in summary
        assert len(facts) == 2
        assert facts[0]["text"] == "App uses FastAPI and asyncpg"
        assert facts[1]["is_pinned"] is True

    def test_extract_json_array_resilience(self):
        """Verifies JSON extraction handles markdown fences and conversational wrappers."""
        raw_markdown = "Here are the facts:\n```json\n[{\"action\": \"ADD\", \"text\": \"fact 1\"}]\n```\nHope this helps!"
        extracted = memory._extract_json_array(raw_markdown)
        assert extracted == '[{"action": "ADD", "text": "fact 1"}]'

    def test_memory_retention_dataset_integrity(self, memory_compaction_data):
        """Validates that benchmark memory dataset contains valid conversation turns and key facts."""
        assert len(memory_compaction_data) > 0
        for item in memory_compaction_data:
            assert "conversation_history" in item
            assert "key_facts_to_retain" in item
            assert len(item["conversation_history"]) >= 4
            assert len(item["key_facts_to_retain"]) >= 3
