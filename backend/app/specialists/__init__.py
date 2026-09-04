"""TrustLens Specialized Reasoning Engine Package"""
from app.specialists.base import BaseSpecialist
from app.specialists.ingestion_agent import IngestionKnowledgeAgent
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

__all__ = [
    "BaseSpecialist",
    "IngestionKnowledgeAgent",
    "ClaimDetective",
    "EvidenceAgent",
    "ContradictionAgent",
    "EntityAgent",
    "TimelineAgent",
    "KnowledgeGapAgent",
    "DataAnalyst",
    "PatternHunter",
    "DocumentComparisonAgent",
    "SynthesisAgent"
]
