"""
tests/test_logger.py — Unit tests for the logging and error diagnostics subsystem.
"""

import os
import sys
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.agent import logger
from src.agent.slash_commands import handle_slash_command


@pytest.fixture(autouse=True)
def reset_logger_state(tmp_path, monkeypatch):
    """Isolates the log directory and file to a temporary directory for each test."""
    temp_log_file = tmp_path / "logs" / "test_losna.log"
    monkeypatch.setenv("LOSNA_LOG_FILE", str(temp_log_file))
    monkeypatch.setenv("LOSNA_LOG_LEVEL", "DEBUG")

    # Reset internal logger state
    logger._LOGGER_INITIALIZED = False
    log_obj = logging.getLogger(logger._LOGGER_NAME)
    for h in list(log_obj.handlers):
        log_obj.removeHandler(h)

    yield temp_log_file

    # Cleanup handlers
    for h in list(log_obj.handlers):
        h.close()
        log_obj.removeHandler(h)
    logger._LOGGER_INITIALIZED = False


def test_setup_logging_creates_file_and_writes(reset_logger_state):
    log_file = reset_logger_state
    log = logger.setup_logging()

    log.info("Test informative message")
    log.warning("Test warning message")
    log.error("Test error message")

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")

    assert "[INFO]" in content
    assert "Test informative message" in content
    assert "[WARNING]" in content
    assert "Test warning message" in content
    assert "[ERROR]" in content
    assert "Test error message" in content


def test_log_exception_captures_traceback(reset_logger_state):
    log_file = reset_logger_state
    log = logger.setup_logging()

    try:
        raise ValueError("Simulated failure in test execution")
    except ValueError as e:
        log.error("Caught exception while testing: %s", e, exc_info=True)

    content = log_file.read_text(encoding="utf-8")
    assert "[ERROR]" in content
    assert "Simulated failure in test execution" in content
    assert "Traceback (most recent call last):" in content
    assert "ValueError: Simulated failure in test execution" in content


def test_read_recent_logs_and_errors_filter(reset_logger_state):
    log = logger.setup_logging()

    log.info("Info line 1")
    log.info("Info line 2")
    log.warning("Warning line 3")
    log.error("Error line 4")
    log.info("Info line 5")

    all_recent = logger.read_recent_logs(lines=10, errors_only=False)
    assert len(all_recent) == 5
    assert "Info line 1" in all_recent[0]

    error_logs = logger.read_recent_logs(lines=10, errors_only=True)
    assert len(error_logs) == 2
    assert "Warning line 3" in error_logs[0]
    assert "Error line 4" in error_logs[1]


def test_clear_logs(reset_logger_state):
    log_file = reset_logger_state
    log = logger.setup_logging()

    log.info("Initial log content to be cleared")
    assert log_file.stat().st_size > 0

    success = logger.clear_logs()
    assert success is True

    # The file should be truncated and then contain only the clear log line
    lines = logger.read_recent_logs(lines=10)
    assert len(lines) == 1
    assert "Log file cleared by user request" in lines[0]


def test_slash_command_logs_path(capsys):
    ctx = {"session_id": 1, "conversation_history": [], "SYSTEM_PROMPT": "", "skills": []}
    handled = handle_slash_command("/logs path", ctx)
    assert handled is True

    captured = capsys.readouterr()
    assert "[Logs]:" in captured.out
    assert "Active log file:" in captured.out


def test_slash_command_logs_display(capsys):
    log = logger.setup_logging()
    log.info("Testing display line")
    log.error("Testing error display line")

    ctx = {"session_id": 1, "conversation_history": [], "SYSTEM_PROMPT": "", "skills": []}
    handled = handle_slash_command("/logs", ctx)
    assert handled is True

    captured = capsys.readouterr()
    assert "Recent Logs" in captured.out
    assert "Testing display line" in captured.out
    assert "Testing error display line" in captured.out


def test_slash_command_logs_errors_filter(capsys):
    log = logger.setup_logging()
    log.info("Should not appear in errors only")
    log.error("Critical failure during API streaming")

    ctx = {"session_id": 1, "conversation_history": [], "SYSTEM_PROMPT": "", "skills": []}
    handled = handle_slash_command("/logs errors", ctx)
    assert handled is True

    captured = capsys.readouterr()
    assert "Error & Traceback Logs" in captured.out
    assert "Critical failure during API streaming" in captured.out
    assert "Should not appear in errors only" not in captured.out


def test_slash_command_logs_clear(capsys):
    log = logger.setup_logging()
    log.info("Message to clear")

    ctx = {"session_id": 1, "conversation_history": [], "SYSTEM_PROMPT": "", "skills": []}
    handled = handle_slash_command("/logs clear", ctx)
    assert handled is True

    captured = capsys.readouterr()
    assert "Logs cleared successfully" in captured.out


def test_unhandled_exception_hook(reset_logger_state):
    log_file = reset_logger_state
    log = logger.setup_logging()

    # Trigger unhandled exception hook
    try:
        raise RuntimeError("Fatal crash outside try-catch")
    except RuntimeError:
        exc_type, exc_val, exc_tb = sys.exc_info()
        with patch.object(sys, "__excepthook__", lambda *a: None):
            sys.excepthook(exc_type, exc_val, exc_tb)

    content = log_file.read_text(encoding="utf-8")
    assert "[CRITICAL]" in content
    assert "FATAL: Unhandled crash in main process" in content
    assert "RuntimeError: Fatal crash outside try-catch" in content
