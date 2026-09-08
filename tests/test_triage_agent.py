"""Smoke tests for the triage agent."""

from app.agents.triage_agent import run_triage
from app.models.schemas import TriageResult


def test_run_triage_returns_structured_result():
    result = run_triage("mujhe halka sar dard hai")
    assert isinstance(result, TriageResult)
    assert result.severity in ("emergency", "moderate", "mild")
    assert isinstance(result.reasoning, str)
