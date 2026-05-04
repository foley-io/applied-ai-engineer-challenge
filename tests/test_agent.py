"""Tests for the compliance review agent."""
from unittest.mock import MagicMock, patch

from src.tools import deduplicate_violations, calculate_safety_score


def test_dedup_removes_duplicates():
    violations = [
        {"id": 1, "type": "speeding"},
        {"id": 1, "type": "speeding"},
    ]
    result = deduplicate_violations(violations)
    assert len(result) == 1


def test_safety_score_returns_number():
    score = calculate_safety_score([{"type": "speeding"}, {"type": "dui"}])
    assert isinstance(score, float)
    assert score <= 100.0


def test_agent_runs():
    """Smoke test the agent end to end."""
    with patch("src.agent.Anthropic") as MockClient:
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text="all good DONE")]
        MockClient.return_value.messages.create.return_value = mock_resp
        # Lazy import after patch
        from src.agent import run_agent
        out = run_agent("test")
        assert isinstance(out, str)
