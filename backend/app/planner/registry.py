"""Lazy in-process specialist registry.

The registry is intentionally a catalog of Python classes, not a collection of
worker processes.  Instances are created only when a capability is selected,
which keeps normal workspace queries and Render startup inexpensive.
"""
from typing import Any, Callable, Dict, List
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
from app.agents.specialists import (
    AnomalyAnalyst,
    DataProfiler,
    EDAAnalyst,
    InsightAnalyst,
    VisualizationAnalyst,
)


class AgentRegistry:
    """
    Central registry of specialized reasoning capabilities.
    Specialists are registered by capability and invoked dynamically.
    """

    def __init__(self):
        self._factories: Dict[str, Callable[[], BaseSpecialist]] = {
            "claim_detective": ClaimDetective,
            "evidence_agent": EvidenceAgent,
            "contradiction_agent": ContradictionAgent,
            "entity_agent": EntityAgent,
            "timeline_agent": TimelineAgent,
            "gap_agent": KnowledgeGapAgent,
            "data_analyst": DataAnalyst,
            "data_profiler": DataProfiler,
            "eda_analyst": EDAAnalyst,
            "insight_analyst": InsightAnalyst,
            "visualization_analyst": VisualizationAnalyst,
            "anomaly_analyst": AnomalyAnalyst,
            "pattern_hunter": PatternHunter,
            "comparison_agent": DocumentComparisonAgent,
            "synthesis_agent": SynthesisAgent,
        }
        self._specialists: Dict[str, BaseSpecialist] = {}

    def get(self, name: str) -> BaseSpecialist:
        if name not in self._factories:
            raise KeyError(f"Specialist '{name}' not found in registry")
        if name not in self._specialists:
            self._specialists[name] = self._factories[name]()
        return self._specialists[name]

    def find_by_capability(self, capability: str) -> List[BaseSpecialist]:
        """Return specialists declaring a capability, constructing on demand."""
        return [
            specialist for name in self._factories
            if capability in (specialist := self.get(name)).capabilities
        ]

    def list_specialists(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": key,
                "name": spec.name,
                "description": spec.description,
                "capabilities": spec.capabilities
            }
            for key in self._factories
            for spec in [self.get(key)]
        ]
