"""Intent dispatch stays selective while preserving structured output."""
import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.planner.planner import AnalysisPlanner


class _Repo:
    def get_semantic_rules(self, _workspace):
        return []


class _Retriever:
    def retrieve(self, *_args, **_kwargs):
        return [
            {"text": "Revenue was 10 percent.", "document_title": "A", "location_info": "Section 1"},
            {"text": "Revenue was 20 percent.", "document_title": "B", "location_info": "Section 1"},
        ]


class _Specialist:
    def __init__(self, name, contexts):
        self.name = name
        self.contexts = contexts

    async def analyze(self, _workspace, context):
        self.contexts[self.name] = context
        values = {
            "entity_agent": {"entities": []},
            "comparison_agent": {"differences": [{"what_changed": "10 to 20"}]},
            "synthesis_agent": {
                "answer": "Comparison complete.", "confidence": 1.0,
                "claims": [], "evidence": [], "contradictions": [],
                "assumptions": [], "unknowns": [], "related_knowledge": {},
            },
        }
        if self.name in {"claim_detective", "evidence_agent"}:
            raise AssertionError(f"{self.name} should not run for comparisons")
        return values.get(self.name, {})


class _Registry:
    def __init__(self):
        self.calls = []
        self.contexts = {}

    def get(self, name):
        self.calls.append(name)
        return _Specialist(name, self.contexts)


def test_comparison_intent_skips_claim_evidence_pipeline():
    planner = object.__new__(AnalysisPlanner)
    planner.repo = _Repo()
    planner.retriever = _Retriever()
    planner.registry = _Registry()

    result = asyncio.run(planner.execute_plan("ws", "Compare the two reports"))

    assert result["intent"] == "COMPARISON_QUERY"
    assert result["related_knowledge"]["comparisons"]
    assert "comparison_agent" in planner.registry.calls
    assert "claim_detective" not in planner.registry.calls
    assert "evidence_agent" not in planner.registry.calls
    assert planner.registry.contexts["synthesis_agent"]["comparisons"]
