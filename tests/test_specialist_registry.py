"""Workspace-specialist registry regression tests."""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.planner.registry import AgentRegistry


def test_registry_contains_workspace_specialists_and_is_lazy():
    registry = AgentRegistry()
    assert registry._specialists == {}
    assert {"claim_detective", "evidence_agent", "comparison_agent", "synthesis_agent"} <= set(registry._factories)
    specialist = registry.get("claim_detective")
    assert specialist.name == "Claim Detective"
    assert set(registry._specialists) == {"claim_detective"}
    assert registry.find_by_capability("answer_contract")[0].name == "Synthesis Specialist"
