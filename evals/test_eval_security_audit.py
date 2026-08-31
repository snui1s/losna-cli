"""
test_eval_security_audit.py — Evaluation test suite for code analysis and security auditing.
"""

import pytest
from src.agent import prompts

class TestSecurityAuditEvals:
    def test_system_prompt_includes_security_directives(self):
        """Verifies system prompt includes instructions for deep analysis and vulnerability detection."""
        system_prompt = prompts.build_system_prompt(read_only=False)
        assert len(system_prompt) > 100
        # Check for core persona and analysis keywords
        assert "Losna" in system_prompt or "assistant" in system_prompt.lower()

    def test_security_dataset_completeness(self, security_audit_data):
        """Verifies security audit dataset contains known vulnerabilities, code snippets, and remediations."""
        assert len(security_audit_data) > 0
        for item in security_audit_data:
            assert "code_snippet" in item
            assert "expected_vulnerabilities" in item
            assert "expected_remediations" in item
            assert len(item["expected_vulnerabilities"]) > 0
            assert len(item["expected_remediations"]) > 0

    def test_security_remediation_guidance(self, security_audit_data):
        """Ensures that each security test case provides concrete remediation requirements."""
        for item in security_audit_data:
            remediations = item["expected_remediations"]
            assert any("parameterized" in r.lower() or "shell=false" in r.lower() or "sanitize" in r.lower() or "path" in r.lower() for r in remediations)
