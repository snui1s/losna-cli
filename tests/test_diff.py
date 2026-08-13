"""
Unit tests for diff_utils module and /diff command integration in Losna CLI.
"""

from unittest.mock import patch, MagicMock
import pytest
from src.agent import diff_utils


class TestDiffUtils:
    def test_get_git_diff_success(self):
        sample_diff = "--- a/main.py\n+++ b/main.py\n@@ -1 +1 @@\n-old\n+new"
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = sample_diff

        with patch("subprocess.run", return_value=mock_proc):
            diff = diff_utils.get_git_diff("main.py")
            assert "main.py" in diff
            assert "+new" in diff

    def test_get_git_diff_error_handling(self):
        with patch("subprocess.run", side_effect=Exception("Git not found")):
            diff = diff_utils.get_git_diff()
            assert "Error retrieving git diff" in diff

    def test_get_git_diff_untracked_file(self):
        sample_untracked = "--- /dev/null\n+++ b/hello.txt\n@@ -0,0 +1 @@\n+hello world"
        mock_proc_empty = MagicMock(returncode=0, stdout="")
        mock_proc_untracked = MagicMock(returncode=0, stdout=sample_untracked)

        with patch("os.path.exists", return_value=True):
            with patch("subprocess.run", side_effect=[mock_proc_empty, mock_proc_untracked]):
                diff = diff_utils.get_git_diff("hello.txt")
                assert "hello.txt" in diff
                assert "+hello world" in diff

    def test_render_session_diff_executes_without_error(self):
        with patch("src.agent.db.get_compaction_state", return_value=(5, "Compacted summary text")):
            with patch("src.agent.db.load_messages", return_value=[{"role": "user", "content": "hi"}]):
                with patch("src.agent.db.load_pinned_memory", return_value=["Fact 1", "Fact 2"]):
                    # Should render cleanly without raising any exceptions
                    diff_utils.render_session_diff(1)
