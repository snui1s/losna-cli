"""
tests/test_timeout_retry.py — Unit tests for API & streaming timeout and retry mechanisms.
"""

import time
import threading
import pytest
from unittest.mock import patch, MagicMock
from src.agent import config
from src.agent.agent_loop import stream_with_timeout, run_agent_loop
from src.agent.slash_commands import handle_slash_command


def test_config_api_timeout_default_and_set(tmp_path):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    fake_rc = fake_home / ".losnarc"

    with patch.object(config, "home_config_path", fake_rc), \
         patch.object(config, "global_config", {}):

        config.set_api_timeout(90)
        assert config.API_TIMEOUT == 90
        assert fake_rc.exists()

        # Enforce minimum of 5 seconds
        config.set_api_timeout(2)
        assert config.API_TIMEOUT == 5


def test_stream_with_timeout_normal():
    def normal_gen():
        yield "chunk 1"
        yield "chunk 2"
        yield "chunk 3"

    results = list(stream_with_timeout(normal_gen(), timeout=1.0))
    assert results == ["chunk 1", "chunk 2", "chunk 3"]


def test_stream_with_timeout_exception_propagates():
    def failing_gen():
        yield "chunk 1"
        raise ValueError("Stream broken")

    stream = stream_with_timeout(failing_gen(), timeout=1.0)
    assert next(stream) == "chunk 1"
    with pytest.raises(ValueError, match="Stream broken"):
        next(stream)


def test_stream_with_timeout_hangs_raises_timeout_error():
    closed = False

    class SlowGen:
        def __iter__(self):
            return self

        def __next__(self):
            # Simulate upstream freeze
            time.sleep(1.0)
            return "too late"

        def close(self):
            nonlocal closed
            closed = True

    gen = SlowGen()
    with pytest.raises(TimeoutError, match="Model stream timed out after 0s with no new response"):
        list(stream_with_timeout(gen, timeout=0.15))

    assert closed is True


def test_slash_command_timeout(capsys):
    ctx = {"session_id": 1, "conversation_history": [], "SYSTEM_PROMPT": "", "skills": []}

    # Query current timeout
    with patch.object(config, "API_TIMEOUT", 60):
        handled = handle_slash_command("/timeout", ctx)
        assert handled is True
        captured = capsys.readouterr()
        assert "Current API_TIMEOUT: 60s" in captured.out

    # Set new valid timeout
    with patch("src.agent.config.set_api_timeout") as mock_set:
        handled = handle_slash_command("/timeout 75", ctx)
        assert handled is True
        mock_set.assert_called_once_with(75)

    # Set invalid timeout (too small)
    handled = handle_slash_command("/timeout 2", ctx)
    assert handled is True
    captured = capsys.readouterr()
    assert "Please provide a timeout of at least 5 seconds" in captured.out

    # Set invalid timeout (non-integer)
    handled = handle_slash_command("/timeout fast", ctx)
    assert handled is True
    captured = capsys.readouterr()
    assert "Please provide a valid positive integer" in captured.out


def test_slash_command_timeout_in_completer():
    from prompt_toolkit.document import Document
    from src.agent import ui
    import inspect

    src = inspect.getsource(ui.get_user_input)
    assert "'/timeout'" in src

    completer = ui.PromptCompleter(['/timeout', '/help', '/clear'])
    completions = list(completer.get_completions(Document('/time'), None))
    assert len(completions) == 1
    assert completions[0].text == '/timeout'


def test_agent_loop_retries_on_timeout_error():
    """Verify that a TimeoutError in the agent loop triggers retry attempts."""
    ctx = {
        "session_id": 999,
        "conversation_history": [{"role": "user", "content": "hello"}],
        "SYSTEM_PROMPT": "You are helpful."
    }

    call_count = 0

    class MockChoice:
        delta = MagicMock(content="Hello after retry!", tool_calls=None)

    class MockChunk:
        choices = [MockChoice()]
        usage = None

    def mock_send(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First attempt hangs / times out
            class HangingGen:
                def __iter__(self):
                    return self
                def __next__(self):
                    evt = threading.Event()
                    evt.wait(0.5)
                    raise StopIteration
                def close(self):
                    pass
            return HangingGen()
        else:
            # Second attempt succeeds
            return [MockChunk()]

    mock_client = MagicMock()
    mock_client.chat.send.side_effect = mock_send

    with patch("src.agent.agent_loop.OpenRouter") as mock_openrouter_cls, \
         patch("src.agent.agent_loop.Spinner"), \
         patch("src.agent.agent_loop.db.get_last_message_id", return_value=0), \
         patch("src.agent.agent_loop.db.delete_messages_after"), \
         patch("src.agent.agent_loop.db.save_message"), \
         patch("src.agent.agent_loop.check_openrouter_health", return_value={"status": "OK"}), \
         patch("src.agent.agent_loop.format_diagnostic_summary", return_value="[Diag OK]"), \
         patch("src.agent.agent_loop.time.sleep"), \
         patch.object(config, "API_TIMEOUT", 0.05), \
         patch.object(config, "MAX_RETRIES", 2), \
         patch.object(config, "RETRY_DELAY", 0.01):

        mock_openrouter_cls.return_value.__enter__.return_value = mock_client

        run_agent_loop(ctx)

        # Should have attempted twice: 1 failed timeout + 1 successful retry
        assert call_count == 2
        assert ctx["conversation_history"][-1]["role"] == "assistant"
        assert ctx["conversation_history"][-1]["content"] == "Hello after retry!"

