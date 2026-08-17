"""
Unit tests for src/agent/config.py

Tests cover:
- Project path resolution (PROJECT_ROOT)
- Configuration constants
- Model name format
- Global config loading and setter functions
"""

import os
import importlib
from unittest.mock import patch

import pytest
import src.agent.config as config_module


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


class TestConfigConstants:
    """Tests for integer constants."""

    @pytest.mark.parametrize("name,expected", [
        ("MAX_RETRIES", 3),
        ("RETRY_DELAY", 2),
        ("MAX_ACTIVE_MESSAGES", 25),
        ("KEEP_RECENT", 4),
    ])
    def test_int_constant(self, name, expected):
        value = getattr(config_module, name)
        assert value == expected
        assert isinstance(value, int)


class TestConfigModels:
    """Tests for model name configuration strings."""

    @pytest.mark.parametrize("attr", ["MODEL_NAME", "COMPACTION_MODEL"])
    def test_model_format(self, attr):
        value = getattr(config_module, attr)
        assert isinstance(value, str)
        assert "/" in value, f"{attr} should be in 'provider/model' format"


class TestConfigToggles:
    """Tests for config toggles and persistence setters."""

    def test_set_read_only_mode(self):
        orig = config_module.READ_ONLY_MODE
        try:
            with patch("src.agent.config.save_global_config") as mock_save:
                config_module.set_read_only_mode(True)
                assert config_module.READ_ONLY_MODE is True
                assert mock_save.called
                config_module.set_read_only_mode(False)
                assert config_module.READ_ONLY_MODE is False
        finally:
            config_module.READ_ONLY_MODE = orig

    def test_set_enter_2_confirm(self):
        orig = config_module.ENTER_2_CONFIRM
        try:
            with patch("src.agent.config.save_global_config") as mock_save:
                config_module.set_enter_2_confirm(True)
                assert config_module.ENTER_2_CONFIRM is True
                assert mock_save.called
                config_module.set_enter_2_confirm(False)
                assert config_module.ENTER_2_CONFIRM is False
        finally:
            config_module.ENTER_2_CONFIRM = orig

    def test_set_max_tool_calls(self):
        orig = config_module.MAX_TOOL_CALLS
        try:
            with patch("src.agent.config.save_global_config") as mock_save:
                config_module.set_max_tool_calls(42)
                assert config_module.MAX_TOOL_CALLS == 42
                assert mock_save.called
        finally:
            config_module.MAX_TOOL_CALLS = orig