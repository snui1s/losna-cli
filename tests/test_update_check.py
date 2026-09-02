import os
import json
import time
from unittest.mock import patch, MagicMock
from src.agent import ui


def test_print_session_header_triggers_update(monkeypatch):
    called = []
    monkeypatch.setattr(ui, "_trigger_async_update_check", lambda: called.append(True))
    with patch("builtins.print"):
        ui.print_session_header(1)
    assert len(called) == 1


def test_update_check_with_loose_ref(tmp_path, monkeypatch, capsys):
    git_dir = tmp_path / ".git"
    git_dir.mkdir(parents=True)
    (git_dir / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    refs_heads = git_dir / "refs" / "heads"
    refs_heads.mkdir(parents=True)
    (refs_heads / "main").write_text("aaa111\n", encoding="utf-8")

    global_dir = tmp_path / "global"
    global_dir.mkdir()

    monkeypatch.setattr(os.path, "expanduser", lambda p: str(global_dir))
    monkeypatch.setattr("src.agent.skills_loader._project_root", lambda: str(tmp_path))

    # Mock urllib.request.urlopen to return a new SHA
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"sha": "bbb222"}).encode()
    mock_urlopen = MagicMock()
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", mock_urlopen):
        ui._trigger_async_update_check()
        # Give thread a moment to finish
        time.sleep(0.3)

    out = capsys.readouterr().out
    assert "A new version of Losna CLI is available" in out


def test_update_check_with_packed_ref(tmp_path, monkeypatch, capsys):
    git_dir = tmp_path / ".git"
    git_dir.mkdir(parents=True)
    (git_dir / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (git_dir / "packed-refs").write_text("# pack-refs with: peeled-tags\naaa111 refs/heads/main\n", encoding="utf-8")

    global_dir = tmp_path / "global"
    global_dir.mkdir()

    monkeypatch.setattr(os.path, "expanduser", lambda p: str(global_dir))
    monkeypatch.setattr("src.agent.skills_loader._project_root", lambda: str(tmp_path))

    # Mock urllib to return a new SHA
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"sha": "bbb222"}).encode()
    mock_urlopen = MagicMock()
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", mock_urlopen):
        ui._trigger_async_update_check()
        time.sleep(0.3)

    out = capsys.readouterr().out
    assert "A new version of Losna CLI is available" in out


if __name__ == "__main__":
    import sys
    import pytest
    print(f"\n  Running Update Check Tests: {__file__}\n")
    sys.exit(pytest.main([__file__, "-v", "-s"]))

