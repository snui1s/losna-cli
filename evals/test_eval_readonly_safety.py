"""
test_eval_readonly_safety.py — Evaluation test suite for Read-Only mode safety & guardrails.
"""

import pytest
from src.agent import config
from src.agent import tools

class TestReadOnlySafetyEvals:
    def test_readonly_schema_filtering_strictness(self):
        """Ensures that no write or modifying tools leak into the available tools schema in read-only mode."""
        readonly_schemas = tools.get_available_tools(read_only=True)
        readonly_names = {t["function"]["name"] for t in readonly_schemas}

        for write_tool in tools.WRITE_TOOL_NAMES:
            assert write_tool not in readonly_names, f"Security Violation: '{write_tool}' found in read-only tool schemas!"

    def test_readonly_dispatch_tool_enforcement(self, readonly_safety_data):
        """Verifies that all destructive intents from safety dataset are completely blocked at runtime."""
        for item in readonly_safety_data:
            intent = item["intent"]
            if intent == "attempt_write_file":
                res = tools.dispatch_tool("edit_local_file", {"filepath": "hack.txt", "content": "bad"}, read_only=True)
                assert "Read-Only Mode is ACTIVE" in res
            elif intent == "attempt_delete_file":
                res = tools.dispatch_tool("delete_local_file", {"filepath": "agent_data.db"}, read_only=True)
                assert "Read-Only Mode is ACTIVE" in res
            elif intent == "attempt_shell_execution":
                res = tools.dispatch_tool("execute_shell_command", {"command": "rm -rf /"}, read_only=True)
                assert "Read-Only Mode is ACTIVE" in res

    def test_zero_tolerance_on_write_tools_in_readonly(self):
        """Asserts zero tolerance for executing write tools when read-only mode is active."""
        for tool_name in ["edit_local_file", "replace_in_file", "delete_local_file", "move_or_rename_file", "execute_shell_command", "git_commit_and_push"]:
            res = tools.dispatch_tool(tool_name, {}, read_only=True)
            assert "Read-Only Mode is ACTIVE" in res
