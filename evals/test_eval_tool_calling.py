"""
test_eval_tool_calling.py — Evaluation test suite for tool selection and parameter schema validity.
"""

import pytest
from src.agent import tools
from src.agent import prompts

class TestToolCallingEvals:
    def test_tool_schema_definitions_validity(self):
        """Verifies that all tools defined in my_tools have valid OpenAI/OpenRouter function schemas."""
        available_tools = tools.get_available_tools(read_only=False)
        assert len(available_tools) > 0

        for tool in available_tools:
            assert "type" in tool and tool["type"] == "function"
            assert "function" in tool
            func = tool["function"]
            assert "name" in func and isinstance(func["name"], str)
            assert "description" in func and len(func["description"]) > 10
            assert "parameters" in func
            params = func["parameters"]
            assert params.get("type") == "object"
            assert "properties" in params

    def test_tool_routing_dataset_coverage(self, tool_routing_data):
        """Evaluates whether all expected tools in the benchmark dataset exist in Losna CLI."""
        assert len(tool_routing_data) > 0
        all_tool_names = {t["function"]["name"] for t in tools.get_available_tools(read_only=False)}

        for item in tool_routing_data:
            expected_tool = item["expected_tool"]
            if expected_tool:
                assert expected_tool in all_tool_names, f"Expected tool '{expected_tool}' not registered in tools.py"

    def test_dispatch_tool_argument_parsing(self, tool_routing_data):
        """Evaluates dispatch_tool handling for each category in dataset."""
        for item in tool_routing_data:
            tool_name = item["expected_tool"]
            if not tool_name:
                continue

            # Build dummy valid arguments based on tool requirements
            dummy_args = {}
            for key in item["expected_args_keys"]:
                if key == "filepath":
                    dummy_args[key] = "README.md"
                elif key == "url":
                    dummy_args[key] = "https://example.com"
                elif key == "ticker":
                    dummy_args[key] = "AAPL"
                elif key == "folder_path":
                    dummy_args[key] = "."
                elif key == "keyword":
                    dummy_args[key] = "test"
                elif key == "start_line":
                    dummy_args[key] = 1
                elif key == "end_line":
                    dummy_args[key] = 10
                elif key == "query":
                    dummy_args[key] = "Python"
                else:
                    dummy_args[key] = "sample"

            # Execute dispatch in test mode (user_confirmed=False so dangerous tools don't actually run)
            res = tools.dispatch_tool(tool_name, dummy_args, read_only=False, user_confirmed=False)
            assert res is not None
            assert not res.startswith("Error: Tool '") or "is blocked" in res or "cancelled" in res.lower()
