"""
Unit test suite for UsageTracker in Losna CLI.
"""

from src.agent.usage_tracker import UsageTracker


def test_usage_tracker_initial_state():
    tracker = UsageTracker()
    assert tracker.total_prompt_tokens == 0
    assert tracker.total_completion_tokens == 0
    assert tracker.total_tokens == 0
    assert tracker.total_cost == 0.0
    assert tracker.call_count == 0
    assert tracker.format_exit_summary() == ""


def test_usage_tracker_record_calls():
    tracker = UsageTracker()
    tracker.record(prompt_tokens=100, completion_tokens=50, cost=0.001)
    tracker.record(prompt_tokens=200, completion_tokens=80, cost=0.002)

    assert tracker.call_count == 2
    assert tracker.total_prompt_tokens == 300
    assert tracker.total_completion_tokens == 130
    assert tracker.total_tokens == 430
    assert abs(tracker.total_cost - 0.003) < 1e-6


def test_usage_tracker_format_outputs():
    tracker = UsageTracker()
    tracker.record(prompt_tokens=500, completion_tokens=150, cost=0.0045)

    footer = tracker.format_turn_footer(duration=1.23)
    assert "1.23s" in footer
    assert "650 tokens" in footer

    summary = tracker.format_summary()
    assert "Session Token Usage" in summary
    assert "500" in summary
    assert "150" in summary
    assert "650" in summary
    assert "$0.0045" in summary

    exit_summary = tracker.format_exit_summary()
    assert "Session Summary" in exit_summary
    assert "650" in exit_summary
