"""
Comprehensive unit test suite for all slash commands and routing in Losna CLI.
"""

import os
from unittest.mock import patch, MagicMock
import pytest
from src.agent import config
from src.agent import db
from src.agent import diff_utils
from src.agent import export_utils
from src.agent import plugin_manager
from src.agent import mention_utils
from src.agent import skills_loader
from src.agent import prompts
from src.agent import ui


class TestSlashCommands:
    # --- 1. /help Command ---
    def test_help_command_skills_list(self):
        skills = skills_loader.list_skills()
        assert isinstance(skills, list)
        for s in skills:
            assert "name" in s
            assert "description" in s

    # --- 2. /sessions Command ---
    def test_sessions_listing(self):
        sid1 = db.create_session("Session Alpha")
        sid2 = db.create_session("Session Beta")

        sessions = db.list_sessions()
        session_ids = [s["id"] for s in sessions]
        assert sid1 in session_ids
        assert sid2 in session_ids

        db.delete_session(sid1)
        db.delete_session(sid2)

    # --- 3. /new <title> Command ---
    def test_new_session_creation(self):
        title = "New Dev Session"
        sid = db.create_session(title)
        assert db.session_exists(sid) is True

        sessions = db.list_sessions()
        meta = next(s for s in sessions if s["id"] == sid)
        assert meta["title"] == title

        db.delete_session(sid)

    # --- 4. /switch <id> Command ---
    def test_switch_session_valid_and_invalid(self):
        sid = db.create_session("Switch Target")
        assert db.session_exists(sid) is True
        assert db.session_exists(999999) is False
        db.delete_session(sid)

    # --- 5. /delete_session <id> Command ---
    def test_delete_session_cascade(self):
        sid = db.create_session("ToDelete")
        db.save_message(sid, "user", "Message before deletion")

        db.delete_session(sid)
        assert db.session_exists(sid) is False
        msgs = db.load_messages(sid)
        assert len(msgs) == 0

    # --- 6. /history Command ---
    def test_history_loading(self):
        sid = db.create_session("History Session")
        db.save_message(sid, "user", "Hello World")
        db.save_message(sid, "assistant", "Hi there")

        msgs = db.load_messages(sid)
        assert len(msgs) == 2
        assert msgs[0]["content"] == "Hello World"
        assert msgs[1]["content"] == "Hi there"

        db.delete_session(sid)

    # --- 7. /model Command ---
    def test_model_name_update(self):
        original_model = config.MODEL_NAME
        test_model = "anthropic/claude-3.5-sonnet"

        config.MODEL_NAME = test_model
        assert config.MODEL_NAME == test_model

        config.MODEL_NAME = original_model

    # --- 8. /readonly Command ---
    def test_readonly_toggle(self):
        config.set_read_only_mode(False)
        assert config.READ_ONLY_MODE is False

        config.set_read_only_mode(True)
        assert config.READ_ONLY_MODE is True

        config.set_read_only_mode(False)
        assert config.READ_ONLY_MODE is False

    # --- 9. /enter2confirm Command ---
    def test_enter2confirm_toggle(self):
        config.set_enter_2_confirm(False)
        assert config.ENTER_2_CONFIRM is False

        config.set_enter_2_confirm(True)
        assert config.ENTER_2_CONFIRM is True

        config.set_enter_2_confirm(False)
        assert config.ENTER_2_CONFIRM is False

    # --- 10. /diff Command ---
    def test_diff_utils_tracked_and_session(self):
        mock_proc = MagicMock(returncode=0, stdout="--- a/main.py\n+++ b/main.py\n+new line")
        with patch("subprocess.run", return_value=mock_proc):
            diff = diff_utils.get_git_diff("src/agent/main.py")
            assert "+new line" in diff

    # --- 11. /pin, /pins, /unpin Commands ---
    def test_pin_and_unpin_lifecycle(self):
        db.save_memory_fact("Core Test Rule: Strict formatting", is_pinned=True)

        pinned = db.load_pinned_memory_with_ids()
        matched = [p for p in pinned if "Strict formatting" in p["text"]]
        assert len(matched) > 0

        target_id = matched[0]["id"]
        success = db.delete_pinned_fact(target_id)
        assert success is True

        updated = db.load_pinned_memory_with_ids()
        assert not any(p["id"] == target_id for p in updated)

    # --- 12. /export Command ---
    def test_export_session_to_markdown(self):
        sid = db.create_session("Export Test Session")
        db.save_message(sid, "user", "What is Losna CLI?")
        db.save_message(sid, "assistant", "Losna CLI is an AI coding assistant.")

        success, filepath = export_utils.export_session_to_markdown(sid)
        assert success is True
        assert os.path.isfile(filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Export Test Session" in content
            assert "What is Losna CLI?" in content

        if os.path.exists(filepath):
            os.remove(filepath)
        db.delete_session(sid)

    # --- 13. Smart @filepath Mentions ---
    def test_mention_utils_extraction(self):
        mentions = mention_utils.extract_file_mentions("Check out @src/agent/main.py and @README.md!")
        assert "src/agent/main.py" in mentions
        assert "README.md" in mentions

    # --- 14. PromptCompleter (/ and @ Autocomplete) ---
    def test_prompt_completer_suggestions(self):
        words = ['/help', '/sessions', '/new', '/switch', '/readonly', '/diff', '/pin', '/export', '/clear']
        completer = ui.PromptCompleter(words)

        doc = MagicMock()
        doc.text_before_cursor = "/sw"
        doc.get_word_before_cursor.return_value = "/sw"

        completions = list(completer.get_completions(doc, None))
        completion_texts = [c.text for c in completions]
        assert "/switch" in completion_texts

    # --- 15. /clear Command ---
    def test_clear_command_autocomplete(self):
        words = ['/clear', '/help']
        completer = ui.PromptCompleter(words)

        doc = MagicMock()
        doc.text_before_cursor = "/cl"
        doc.get_word_before_cursor.return_value = "/cl"

        completions = list(completer.get_completions(doc, None))
        completion_texts = [c.text for c in completions]
        assert "/clear" in completion_texts

    # --- 16. /max_tool_calls Command ---
    def test_max_tool_calls_setting(self):
        original_val = config.MAX_TOOL_CALLS

        config.set_max_tool_calls(42)
        assert config.MAX_TOOL_CALLS == 42

        # Reset back
        config.set_max_tool_calls(original_val)

    # --- 17. Skill Enable / Disable Toggle ---
    def test_skill_enable_disable_toggle(self):
        skill_name = "caveman"
        with patch("src.agent.config.save_global_config"):
            config.disable_skill(skill_name)
            assert config.is_skill_disabled(skill_name) is True

            config.enable_skill(skill_name)
            assert config.is_skill_disabled(skill_name) is False

    # --- 18. /ls Command ---
    def test_ls_command_autocomplete(self):
        words = ['/ls', '/help']
        completer = ui.PromptCompleter(words)

        doc = MagicMock()
        doc.text_before_cursor = "/l"
        doc.get_word_before_cursor.return_value = "/l"

        completions = list(completer.get_completions(doc, None))
        completion_texts = [c.text for c in completions]
        assert "/ls" in completion_texts

    # --- 19. /cd Command ---
    def test_cd_command_autocomplete(self):
        words = ['/cd', '/help']
        completer = ui.PromptCompleter(words)

        doc = MagicMock()
        doc.text_before_cursor = "/c"
        doc.get_word_before_cursor.return_value = "/c"

        completions = list(completer.get_completions(doc, None))
        completion_texts = [c.text for c in completions]
        assert "/cd" in completion_texts

    def test_cd_directory_autocompletion(self, monkeypatch):
        monkeypatch.chdir(config.PROJECT_ROOT)
        words = ['/cd', '/help']
        completer = ui.PromptCompleter(words)

        doc = MagicMock()
        doc.text_before_cursor = "/cd "
        doc.get_word_before_cursor.return_value = ""

        completions = list(completer.get_completions(doc, None))
        completion_texts = [c.text for c in completions]
        assert "src/" in completion_texts or "tests/" in completion_texts

    # --- 20. Auto-Detected AI Context ---
    def test_auto_ai_context_detection(self, tmp_path, monkeypatch):
        test_ai_file = tmp_path / "ai.txt"
        test_ai_file.write_text("# Project AI Instructions\nWrite clean python.", encoding="utf-8")
        monkeypatch.chdir(tmp_path)

        fname, rel_path, content = prompts.load_auto_ai_context()
        assert fname == "ai.txt"
        assert "Write clean python" in content
