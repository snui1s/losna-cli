"""
Unit tests for /enter2confirm slash command and configuration toggle.
"""

import pytest
from src.agent import config


class TestEnter2Confirm:
    def test_set_enter_2_confirm_config(self):
        config.set_enter_2_confirm(True)
        assert config.ENTER_2_CONFIRM is True

        config.set_enter_2_confirm(False)
        assert config.ENTER_2_CONFIRM is False
