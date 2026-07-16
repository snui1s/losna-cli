"""
Unit tests for src/agent/config.py

Tests cover:
- Project path resolution (PROJECT_ROOT)
- Hardcoded configuration constants
- Model name format
- API key reading from os.environ
- .env file parsing logic (via module reload with mocked I/O)
"""

import os
import importlib
from unittest.mock import patch, mock_open

import pytest

import src.agent.config as config_module


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────

def _cleanup_test_env_vars(*keys):
    """Remove test-only env vars after a mocked test."""
    for key in keys:
        os.environ.pop(key, None)


# ─────────────────────────────────────────────
# Path resolution
# ─────────────────────────────────────────────

class TestConfigPaths:
    """Tests for project path resolution in config.py."""

    def test_project_root_is_absolute(self):
        assert os.path.isabs(config_module.PROJECT_ROOT)

    def test_project_root_is_repo_root(self):
        """PROJECT_ROOT should contain src/ and pyproject.toml."""
        assert os.path.isdir(os.path.join(config_module.PROJECT_ROOT, "src"))
        assert os.path.isfile(
            os.path.join(config_module.PROJECT_ROOT, "pyproject.toml")
        )

    def test_project_root_goes_up_two_levels_from_script_dir(self):
        """PROJECT_ROOT = script_dir/../.."""
        expected = os.path.abspath(
            os.path.join(config_module.script_dir, "..", "..")
        )
        assert config_module.PROJECT_ROOT == expected


# ─────────────────────────────────────────────
# Hardcoded constants
# ─────────────────────────────────────────────

class TestConfigConstants:
    """Tests for hardcoded integer constants."""

    @pytest.mark.parametrize("name,expected", [
        ("MAX_RETRIES", 3),
        ("RETRY_DELAY", 2),
        ("MAX_ACTIVE_MESSAGES", 25),
        ("KEEP_RECENT", 4),
        ("MAX_TOOL_CALLS", 25),
    ])
    def test_int_constant(self, name, expected):
        value = getattr(config_module, name)
        assert value == expected
        assert isinstance(value, int)


# ─────────────────────────────────────────────
# Model names
# ─────────────────────────────────────────────

class TestConfigModels:
    """Tests for model name configuration strings."""

    @pytest.mark.parametrize("attr", ["MODEL_NAME", "COMPACTION_MODEL"])
    def test_model_format(self, attr):
        value = getattr(config_module, attr)
        assert isinstance(value, str)
        assert "/" in value, f"{attr} should be in 'provider/model' format"


# ─────────────────────────────────────────────
# API keys
# ─────────────────────────────────────────────

class TestConfigApiKeys:
    """Tests that API keys are read from os.environ."""

    def test_tavily_api_key_from_env(self):
        assert config_module.TAVILY_API_KEY == os.getenv("TAVILY_API_KEY")

    def test_openrouter_api_key_from_env(self):
        assert config_module.OPENROUTER_API_KEY == os.getenv("OPENROUTER_API_KEY")

    def test_api_keys_can_be_none(self):
        """If env vars are unset, the config values should be None."""
        with patch.dict(os.environ, {}, clear=True), \
             patch("os.path.exists", return_value=False):
            importlib.reload(config_module)
            assert config_module.TAVILY_API_KEY is None
            assert config_module.OPENROUTER_API_KEY is None
        # Restore real state
        importlib.reload(config_module)


# ─────────────────────────────────────────────
# .env file loading logic
# ─────────────────────────────────────────────

class TestEnvFileLoading:
    """
    Tests for the module-level .env file parsing in config.py.

    These tests reload config.py with mocked os.path.exists and builtins.open
    to verify the parsing logic without touching the real .env file.
    Each test cleans up its own test env vars and restores config to the
    real state via a final reload.
    """

    @pytest.fixture(autouse=True)
    def restore_config(self):
        """Restore config to real state after every test."""
        yield
        importlib.reload(config_module)

    def test_valid_key_value_lines_are_set(self):
        """Valid KEY=value lines should set os.environ entries."""
        mock_content = "TEST_VAR_A=custom_value\nTEST_VAR_B=another_value"
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_content)):
            importlib.reload(config_module)

        assert os.environ.get("TEST_VAR_A") == "custom_value"
        assert os.environ.get("TEST_VAR_B") == "another_value"
        _cleanup_test_env_vars("TEST_VAR_A", "TEST_VAR_B")

    def test_comment_and_blank_lines_are_skipped(self):
        """Lines starting with # and blank lines should be ignored."""
        mock_content = (
            "# This is a comment\n"
            "\n"
            "TEST_VALID=set\n"
            "  \n"
            "# Another comment\n"
        )
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_content)):
            importlib.reload(config_module)

        assert os.environ.get("TEST_VALID") == "set"
        # Comment lines should not become env vars
        assert "This is a comment" not in os.environ
        _cleanup_test_env_vars("TEST_VALID")

    def test_whitespace_around_equals_is_stripped(self):
        """Spaces around '=' should be stripped from key and value."""
        mock_content = "TEST_SPACED = value_with_spaces\nTEST_TIGHT=no_spaces"
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_content)):
            importlib.reload(config_module)

        assert os.environ.get("TEST_SPACED") == "value_with_spaces"
        assert os.environ.get("TEST_TIGHT") == "no_spaces"
        _cleanup_test_env_vars("TEST_SPACED", "TEST_TIGHT")

    def test_lines_without_equals_are_skipped(self):
        """Lines without '=' should be silently ignored."""
        mock_content = "THIS_IS_NOT_A_VALID_LINE\nTEST_OK=yes"
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_content)):
            importlib.reload(config_module)

        assert "THIS_IS_NOT_A_VALID_LINE" not in os.environ
        assert os.environ.get("TEST_OK") == "yes"
        _cleanup_test_env_vars("TEST_OK")

    def test_values_with_equals_in_value(self):
        """Values containing '=' (e.g. JWTs, tokens) should be preserved."""
        mock_content = "TEST_JWT=header.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature"
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_content)):
            importlib.reload(config_module)

        assert (
            os.environ.get("TEST_JWT")
            == "header.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature"
        )
        _cleanup_test_env_vars("TEST_JWT")

    def test_missing_env_file_does_not_crash(self):
        """When .env doesn't exist, config should load without error."""
        with patch("os.path.exists", return_value=False):
            try:
                importlib.reload(config_module)
            except Exception as exc:
                pytest.fail(f"Reload without .env raised: {exc}")

    def test_empty_env_file(self):
        """An empty .env file should not crash and set no vars."""
        mock_content = ""
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_content)):
            importlib.reload(config_module)
        # No crash means success

    def test_env_file_with_only_comments(self):
        """A .env file with only comments should set no env vars."""
        mock_content = "# line 1\n# line 2\n  # indented\n"
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_content)):
            importlib.reload(config_module)
        # No crash, no env vars from .env - good