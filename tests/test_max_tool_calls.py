import os
from unittest.mock import patch, MagicMock
from src.agent.agent_loop import run_agent_loop
from src.agent import config


class DummyChunk:
    def __init__(self, content=None, tool_calls=None):
        self.choices = [MagicMock()]
        self.choices[0].delta = MagicMock()
        self.choices[0].delta.content = content
        self.choices[0].delta.tool_calls = tool_calls
        self.usage = None


def test_max_tool_calls_continue(monkeypatch):
    """Test that selecting 'c' (Continue) extends the tool limit and executes tools."""
    monkeypatch.setattr(config, "MAX_TOOL_CALLS", 1)
    monkeypatch.setattr(config, "MAX_RETRIES", 1)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    ctx = {
        "session_id": 1,
        "conversation_history": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Test tool calls"}
        ],
        "SYSTEM_PROMPT": "You are a helpful assistant."
    }

    tool_call_delta_1 = MagicMock()
    tool_call_delta_1.index = 0
    tool_call_delta_1.id = "call_123"
    tool_call_delta_1.function = MagicMock()
    tool_call_delta_1.function.name = "get_current_time"
    tool_call_delta_1.function.arguments = "{}"

    tool_call_delta_2 = MagicMock()
    tool_call_delta_2.index = 0
    tool_call_delta_2.id = "call_124"
    tool_call_delta_2.function = MagicMock()
    tool_call_delta_2.function.name = "get_current_time"
    tool_call_delta_2.function.arguments = "{}"

    stream_1 = [DummyChunk(content=None, tool_calls=[tool_call_delta_1])]
    stream_2 = [DummyChunk(content=None, tool_calls=[tool_call_delta_2])]
    stream_3 = [DummyChunk(content="Final synthesized answer.", tool_calls=None)]

    mock_client = MagicMock()
    mock_client.chat.send.side_effect = [iter(stream_1), iter(stream_2), iter(stream_3)]

    with patch("src.agent.agent_loop.OpenRouter") as MockOpenRouter, \
         patch("src.agent.agent_loop.db.save_message"), \
         patch("src.agent.agent_loop.dispatch_tool", return_value="2026-08-27 10:00:00"), \
         patch("builtins.input", return_value="c"), \
         patch("sys.stdin.isatty", return_value=True):

        MockOpenRouter.return_value.__enter__.return_value = mock_client
        run_agent_loop(ctx)

    # Verify conversation history has assistant tool call, tool result, and final answer
    roles = [m["role"] for m in ctx["conversation_history"]]
    assert "tool" in roles
    assert ctx["conversation_history"][-1]["content"] == "Final synthesized answer."


def test_max_tool_calls_summarize(monkeypatch):
    """Test that selecting 's' (Summarize) stops tool execution and requests synthesis."""
    monkeypatch.setattr(config, "MAX_TOOL_CALLS", 1)
    monkeypatch.setattr(config, "MAX_RETRIES", 1)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    ctx = {
        "session_id": 1,
        "conversation_history": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Test tool calls"}
        ],
        "SYSTEM_PROMPT": "You are a helpful assistant."
    }

    tool_call_delta_1 = MagicMock()
    tool_call_delta_1.index = 0
    tool_call_delta_1.id = "call_456"
    tool_call_delta_1.function = MagicMock()
    tool_call_delta_1.function.name = "list_directory"
    tool_call_delta_1.function.arguments = "{}"

    tool_call_delta_2 = MagicMock()
    tool_call_delta_2.index = 0
    tool_call_delta_2.id = "call_457"
    tool_call_delta_2.function = MagicMock()
    tool_call_delta_2.function.name = "list_directory"
    tool_call_delta_2.function.arguments = "{}"

    stream_1 = [DummyChunk(content=None, tool_calls=[tool_call_delta_1])]
    stream_2 = [DummyChunk(content=None, tool_calls=[tool_call_delta_2])]
    stream_3 = [DummyChunk(content="Summary of what was gathered.", tool_calls=None)]

    mock_client = MagicMock()
    mock_client.chat.send.side_effect = [iter(stream_1), iter(stream_2), iter(stream_3)]

    with patch("src.agent.agent_loop.OpenRouter") as MockOpenRouter, \
         patch("src.agent.agent_loop.db.save_message"), \
         patch("builtins.input", return_value="s"), \
         patch("sys.stdin.isatty", return_value=True):

        MockOpenRouter.return_value.__enter__.return_value = mock_client
        run_agent_loop(ctx)

    assert ctx["conversation_history"][-1]["content"] == "Summary of what was gathered."


def test_max_tool_calls_abort(monkeypatch):
    """Test that selecting 'a' (Abort) reverts to the safe history backup."""
    monkeypatch.setattr(config, "MAX_TOOL_CALLS", 1)
    monkeypatch.setattr(config, "MAX_RETRIES", 1)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    initial_history = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Test tool calls"}
    ]
    ctx = {
        "session_id": 1,
        "conversation_history": list(initial_history),
        "SYSTEM_PROMPT": "You are a helpful assistant."
    }

    tool_call_delta_1 = MagicMock()
    tool_call_delta_1.index = 0
    tool_call_delta_1.id = "call_789"
    tool_call_delta_1.function = MagicMock()
    tool_call_delta_1.function.name = "list_directory"
    tool_call_delta_1.function.arguments = "{}"

    tool_call_delta_2 = MagicMock()
    tool_call_delta_2.index = 0
    tool_call_delta_2.id = "call_790"
    tool_call_delta_2.function = MagicMock()
    tool_call_delta_2.function.name = "list_directory"
    tool_call_delta_2.function.arguments = "{}"

    stream_1 = [DummyChunk(content=None, tool_calls=[tool_call_delta_1])]
    stream_2 = [DummyChunk(content=None, tool_calls=[tool_call_delta_2])]

    mock_client = MagicMock()
    mock_client.chat.send.side_effect = [iter(stream_1), iter(stream_2)]

    with patch("src.agent.agent_loop.OpenRouter") as MockOpenRouter, \
         patch("src.agent.agent_loop.db.save_message"), \
         patch("builtins.input", return_value="a"), \
         patch("sys.stdin.isatty", return_value=True):

        MockOpenRouter.return_value.__enter__.return_value = mock_client
        run_agent_loop(ctx)

    # Verify conversation history was cleanly reverted to initial state
    assert len(ctx["conversation_history"]) == 2
    assert ctx["conversation_history"] == initial_history


def test_max_tool_calls_non_interactive(monkeypatch):
    """Test that in non-interactive mode, it defaults to summarize and completes."""
    monkeypatch.setattr(config, "MAX_TOOL_CALLS", 1)
    monkeypatch.setattr(config, "MAX_RETRIES", 1)

    ctx = {
        "session_id": 1,
        "conversation_history": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Test non-interactive"}
        ],
        "SYSTEM_PROMPT": "You are a helpful assistant."
    }

    tool_call_delta_1 = MagicMock()
    tool_call_delta_1.index = 0
    tool_call_delta_1.id = "call_991"
    tool_call_delta_1.function = MagicMock()
    tool_call_delta_1.function.name = "list_directory"
    tool_call_delta_1.function.arguments = "{}"

    tool_call_delta_2 = MagicMock()
    tool_call_delta_2.index = 0
    tool_call_delta_2.id = "call_992"
    tool_call_delta_2.function = MagicMock()
    tool_call_delta_2.function.name = "list_directory"
    tool_call_delta_2.function.arguments = "{}"

    stream_1 = [DummyChunk(content=None, tool_calls=[tool_call_delta_1])]
    stream_2 = [DummyChunk(content=None, tool_calls=[tool_call_delta_2])]
    stream_3 = [DummyChunk(content="Non-interactive synthesized summary.", tool_calls=None)]

    mock_client = MagicMock()
    mock_client.chat.send.side_effect = [iter(stream_1), iter(stream_2), iter(stream_3)]

    with patch("src.agent.agent_loop.OpenRouter") as MockOpenRouter, \
         patch("src.agent.agent_loop.db.save_message"), \
         patch("sys.stdin.isatty", return_value=False):

        MockOpenRouter.return_value.__enter__.return_value = mock_client
        run_agent_loop(ctx)

    assert ctx["conversation_history"][-1]["content"] == "Non-interactive synthesized summary."
