"""
Unit tests for /pin, /unpin, /pins, and /export slash commands and helpers.
"""

import os
from unittest.mock import patch
from src.agent import db
from src.agent import export_utils


class TestPinAndExport:
    def test_pin_and_unpin_lifecycle(self):
        # 1. Pin a test fact
        db.save_memory_fact("Test core rule: Always use pytest", is_pinned=True)

        # 2. Verify it appears in load_pinned_memory_with_ids
        pinned = db.load_pinned_memory_with_ids()
        matched = [p for p in pinned if "Always use pytest" in p["text"]]
        assert len(matched) > 0

        target_id = matched[0]["id"]

        # 3. Unpin it by ID
        success = db.delete_pinned_fact(target_id)
        assert success is True

        # 4. Verify it's no longer pinned
        updated_pinned = db.load_pinned_memory_with_ids()
        assert not any(p["id"] == target_id for p in updated_pinned)

    def test_export_session_to_markdown(self):
        # Create a test session and save a dummy message
        sid = db.create_session("Test Export Session")
        db.save_message(sid, "user", "Hello agent!")
        db.save_message(sid, "assistant", "Hello user!")

        # Export to markdown
        success, filepath = export_utils.export_session_to_markdown(sid)
        assert success is True
        assert os.path.isfile(filepath)

        # Verify content inside exported markdown
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Test Export Session" in content
            assert "Hello agent!" in content
            assert "Hello user!" in content

        # Cleanup test file
        if os.path.exists(filepath):
            os.remove(filepath)
        db.delete_session(sid)
