"""
Unit tests for Read-Only Mode in Losna CLI.

Tests cover:
- Tool filtering with get_available_tools(read_only=True/False)
- Security block in dispatch_tool when read_only=True
- Read-only allowed tools pass through dispatch_tool
- System prompt generation includes Read-Only Mode directive when active
- Config state modification via set_read_only_mode
"""

import pytest
from src.agent import config
from src.agent import prompts
from src.agent import tools


class TestReadOnlyMode:
    def test_set_read_only_mode_config(self):
        config.set_read_only_mode(True)
        assert config.READ_ONLY_MODE is True

        config.set_read_only_mode(False)
        assert config.READ_ONLY_MODE is False

    def test_get_available_tools_filtering(self):
        full_tools = tools.get_available_tools(read_only=False)
        readonly_tools = tools.get_available_tools(read_only=True)

        full_names = [t["function"]["name"] for t in full_tools]
        readonly_names = [t["function"]["name"] for t in readonly_tools]

        # Verify all tools in readonly list are in READ_ONLY_TOOL_NAMES
        for name in readonly_names:
            assert name in tools.READ_ONLY_TOOL_NAMES

        # Verify write tools are excluded when read_only=True
        assert "edit_local_file" not in readonly_names
        assert "execute_shell_command" not in readonly_names
        assert "delete_local_file" not in readonly_names
        assert "replace_in_file" not in readonly_names
        assert "move_or_rename_file" not in readonly_names
        assert "git_commit_and_push" not in readonly_names

        # Verify read tools are present
        assert "read_local_file" in readonly_names
        assert "list_directory" in readonly_names
        assert "search_in_files" in readonly_names

    def test_dispatch_tool_blocks_write_operations(self):
        # Destructive / Modifying tool calls should return security block in Read-Only Mode
        res_edit = tools.dispatch_tool("edit_local_file", {"filepath": "test.txt", "content": "hello"}, read_only=True)
        assert "Read-Only Mode is ACTIVE" in res_edit

        res_exec = tools.dispatch_tool("execute_shell_command", {"command": "echo 1"}, read_only=True)
        assert "Read-Only Mode is ACTIVE" in res_exec

        res_del = tools.dispatch_tool("delete_local_file", {"filepath": "test.txt"}, read_only=True)
        assert "Read-Only Mode is ACTIVE" in res_del

        res_replace = tools.dispatch_tool("replace_in_file", {"filepath": "test.txt", "old_text": "a", "new_text": "b"}, read_only=True)
        assert "Read-Only Mode is ACTIVE" in res_replace

    def test_dispatch_tool_allows_read_operations(self):
        # Read-only tool call should execute normally
        res_time = tools.dispatch_tool("get_current_time", {}, read_only=True)
        assert res_time != ""
        assert "Read-Only Mode is ACTIVE" not in res_time

    def test_system_prompt_includes_readonly_directive(self):
        prompt_normal = prompts.build_system_prompt(read_only=False)
        assert "[READ-ONLY MODE ACTIVE]" not in prompt_normal

        prompt_readonly = prompts.build_system_prompt(read_only=True)
        assert "[READ-ONLY MODE ACTIVE]" in prompt_readonly
