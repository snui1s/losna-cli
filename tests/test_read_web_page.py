"""
Unit tests for read_web_page tool in src/agent/tools.py.

Tests cover:
- Invalid URL validation
- Trafilatura extraction mocked success
- Trafilatura extraction mocked failure/empty
- Tool registration in my_tools and READ_ONLY_TOOL_NAMES
"""

from unittest.mock import patch
from src.agent import tools


class TestReadWebPageTool:
    def test_invalid_url_validation(self):
        res = tools.read_web_page("ftp://invalid-url.com")
        assert "Invalid URL" in res

        res_empty = tools.read_web_page("")
        assert "Invalid URL" in res_empty

    def test_read_web_page_success(self):
        sample_html = "<html><body><h1>Test Article</h1><p>This is a test blog post content.</p></body></html>"
        sample_text = "Test Article\nThis is a test blog post content."

        with patch("trafilatura.fetch_url", return_value=sample_html):
            with patch("trafilatura.extract", return_value=sample_text):
                res = tools.read_web_page("https://example.com/blog/test-post")
                assert "Test Article" in res
                assert "test blog post content" in res

    def test_read_web_page_fetch_failure(self):
        with patch("trafilatura.fetch_url", return_value=None):
            res = tools.read_web_page("https://example.com/not-found")
            assert "Could not fetch web page" in res

    def test_tool_registration(self):
        assert "read_web_page" in tools.READ_ONLY_TOOL_NAMES

        registered_tools = [t["function"]["name"] for t in tools.my_tools]
        assert "read_web_page" in registered_tools
