"""
Unit tests for mention_utils module and @filepath mentions in Losna CLI.
"""

from unittest.mock import patch, mock_open
import pytest
from src.agent import mention_utils


class TestMentionUtils:
    def test_extract_file_mentions_valid(self):
        text = "Check out @README.md and @src/agent/main.py for details."

        with patch("os.path.isfile", return_value=True):
            with patch("os.path.realpath", side_effect=lambda x: f"/project/{x}"):
                mentions = mention_utils.extract_file_mentions(text)
                assert "README.md" in mentions
                assert "src/agent/main.py" in mentions

    def test_extract_file_mentions_non_existent(self):
        text = "Check out @non_existent_file.py please."

        with patch("os.path.isfile", return_value=False):
            mentions = mention_utils.extract_file_mentions(text)
            assert len(mentions) == 0

    def test_load_file_attachments(self):
        sample_content = "def hello(): pass"
        m_open = mock_open(read_data=sample_content)

        with patch("builtins.open", m_open):
            attachments = mention_utils.load_file_attachments(["test.py"])
            assert len(attachments) == 1
            assert attachments[0]["path"] == "test.py"
            assert attachments[0]["content"] == sample_content

    def test_build_mention_prompt_block(self):
        attachments = [{"path": "hello.txt", "content": "Hi star"}]
        block = mention_utils.build_mention_prompt_block(attachments)
        assert "[Attached File Context from @mentions]:" in block
        assert "hello.txt" in block
        assert "Hi star" in block
