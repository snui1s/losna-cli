import io
import sys
from unittest.mock import patch
from src.agent import db
from src.agent import ui
from src.agent import session


def test_db_recent_messages_and_preview(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_recent.db")
    monkeypatch.setattr(db, "DB_PATH", test_db)

    # Setup test DB tables in isolated temporary database
    db.init_db()
    sid = db.create_session("Test UX Preview")

    # Initially no messages
    assert db.get_last_session_message(sid) is None
    assert db.get_recent_messages(sid) == []

    # Add messages
    db.save_message(sid, "user", "Hello AI")
    db.save_message(sid, "assistant", "Hello human, how can I help?")
    db.save_message(sid, "user", "What is the capital of Thailand?")
    db.save_message(sid, "assistant", "The capital of Thailand is Bangkok.")

    last_msg = db.get_last_session_message(sid)
    assert last_msg is not None
    assert last_msg["role"] == "assistant"
    assert "Bangkok" in last_msg["content"]

    recent_3 = db.get_recent_messages(sid, limit=3)
    assert len(recent_3) == 3
    assert recent_3[0]["content"] == "Hello human, how can I help?"
    assert recent_3[1]["content"] == "What is the capital of Thailand?"
    assert recent_3[2]["content"] == "The capital of Thailand is Bangkok."

    sessions_with_preview = db.list_sessions_with_preview()
    target_s = next((s for s in sessions_with_preview if s["id"] == sid), None)
    assert target_s is not None
    assert target_s["msg_count"] >= 4
    assert target_s["last_message"] is not None
    assert target_s["last_message"]["role"] == "assistant"


def test_ui_print_recent_messages_preview():
    messages = [
        {"role": "user", "content": "How to optimize Python loops?"},
        {"role": "assistant", "content": "You can use list comprehensions or vectorization.\nHere is an example..."}
    ]

    captured_out = io.StringIO()
    with patch("sys.stdout", captured_out):
        ui.print_recent_messages_preview(messages, session_id=42, session_title="Optimization Chat")

    output = captured_out.getvalue()
    assert "Session [42]" in output
    assert "Optimization Chat" in output
    assert "How to optimize Python loops?" in output
    assert "You can use list comprehensions" in output


def test_session_select_default_on_enter(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_session_select.db")
    monkeypatch.setattr(db, "DB_PATH", test_db)

    db.init_db()
    sid = db.create_session("Default Session Test")
    db.save_message(sid, "user", "First question")

    # Simulate user pressing Enter (empty input "") to pick default session
    with patch("builtins.input", return_value=""), \
         patch("src.agent.db.list_sessions_with_preview", return_value=[{"id": sid, "title": "Default Session Test", "updated_at": "2026-08-27 10:00:00", "msg_count": 1, "last_message": {"role": "user", "content": "First question"}}]):

        chosen_id, history = session.select_session()
        assert chosen_id == sid
        assert len(history) >= 2


def test_session_preview_with_empty_or_whitespace_last_message(tmp_path, monkeypatch):
    """Test that session selection and preview handle empty or tool-only assistant messages without crashing."""
    test_db = str(tmp_path / "test_empty_msg.db")
    monkeypatch.setattr(db, "DB_PATH", test_db)

    db.init_db()
    sid = db.create_session("Tool Only Session")
    # Save a tool-only assistant message (empty content)
    db.save_message(sid, "assistant", "", tool_calls_json='[{"id": "call_1"}]')

    with patch("builtins.input", return_value=str(sid)):
        chosen_id, history = session.select_session()
        assert chosen_id == sid

