"""Agent Registry cataloging specialized reasoning capabilities"""
from typing import Any, Dict, List, Type
from app.specialists.base import BaseSpecialist
from app.specialists.claim_detective import ClaimDetective
from app.specialists.evidence_agent import EvidenceAgent
from app.specialists.contradiction_agent import ContradictionAgent
from app.specialists.entity_agent import EntityAgent
from app.specialists.timeline_agent import TimelineAgent
from app.specialists.gap_agent import KnowledgeGapAgent
from app.specialists.data_analyst import DataAnalyst
from app.specialists.pattern_hunter import PatternHunter
from app.specialists.comparison_agent import DocumentComparisonAgent
from app.specialists.synthesis_agent import SynthesisAgent


class AgentRegistry:
    """
    Central registry of specialized reasoning capabilities.
    Specialists are registered by capability and invoked dynamically.
    """

    def __init__(self):
        self._specialists: Dict[str, BaseSpecialist] = {
            "claim_detective": ClaimDetective(),
            "evidence_agent": EvidenceAgent(),
            "contradiction_agent": ContradictionAgent(),
            "entity_agent": EntityAgent(),
            "timeline_agent": TimelineAgent(),
            "gap_agent": KnowledgeGapAgent(),
            "data_analyst": DataAnalyst(),
            "pattern_hunter": PatternHunter(),
            "comparison_agent": DocumentComparisonAgent(),
            "synthesis_agent": SynthesisAgent()
        }

    def get(self, name: str) -> BaseSpecialist:
        if name not in self._specialists:
            raise KeyError(f"Specialist '{name}' not found in registry")
        return self._specialists[name]

    def list_specialists(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": key,
                "name": spec.name,
                "description": spec.description,
                "capabilities": spec.capabilities
            }
            for key, spec in self._specialists.items()
        ]
