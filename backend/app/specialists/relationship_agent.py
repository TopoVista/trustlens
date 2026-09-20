"""Evidence-backed relationship extraction for the workspace intelligence graph.

The agent is intentionally conservative: explicit relation language can create a
semantic edge, while simple co-occurrence is only retained as a low-confidence
``ASSOCIATED_WITH`` relationship with the source claim as provenance.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.knowledge.repository import KnowledgeRepository


_RELATION_PATTERNS = (
    ("DEPENDS_ON", re.compile(r"\bdepends? on\b|\brequires?\b", re.IGNORECASE), 0.88),
    ("AFFECTS", re.compile(r"\baffects?\b|\bimpacts?\b|\binfluences?\b", re.IGNORECASE), 0.84),
    ("CONTRIBUTES_TO", re.compile(r"\bcontributes? to\b", re.IGNORECASE), 0.82),
    # Causation is emitted only where the source uses explicit causal language.
    ("CAUSES", re.compile(r"\bcauses?\b|\bcaused\b|\bled to\b", re.IGNORECASE), 0.86),
)


class RelationshipAgent:
    """Find meaningful entity relationships from persisted, source-backed claims."""

    def __init__(self, repo: Optional[KnowledgeRepository] = None):
        self.repo = repo or KnowledgeRepository()

    @staticmethod
    def _mentioned_entities(statement: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        text = (statement or "").lower()
        mentioned = []
        for entity in entities:
            names = [entity.get("name", ""), *entity.get("aliases", [])]
            if any(name and re.search(rf"\b{re.escape(str(name).lower())}\b", text) for name in names):
                mentioned.append(entity)
        return mentioned

    @staticmethod
    def _classify(statement: str) -> tuple[str, float, str]:
        for relation, pattern, confidence in _RELATION_PATTERNS:
            if pattern.search(statement or ""):
                return relation, confidence, "EXPLICIT_SOURCE_RELATION"
        return "ASSOCIATED_WITH", 0.55, "HEURISTIC"

    def enrich_document(self, workspace_id: str, document_id: str) -> Dict[str, Any]:
        """Persist only explainable entity pairs from claims owned by one document."""
        entities = self.repo.get_entities(workspace_id)
        claims = [claim for claim in self.repo.get_claims(workspace_id) if claim.get("document_id") == document_id]
        accepted: List[Dict[str, Any]] = []
        rejected = 0

        for claim in claims:
            statement = claim.get("statement", "")
            mentioned = self._mentioned_entities(statement, entities)
            if len(mentioned) < 2:
                continue
            relation, confidence, provenance = self._classify(statement)
            for index, source in enumerate(mentioned[:-1]):
                for target in mentioned[index + 1:]:
                    # The old adjacent ``related_to`` output is intentionally
                    # not persisted. Each retained pair points back to the claim.
                    self.repo.add_relationship(
                        workspace_id,
                        source["id"],
                        target["id"],
                        relation,
                        evidence_text=statement,
                    )
                    accepted.append({
                        "source_entity_id": source["id"],
                        "target_entity_id": target["id"],
                        "relation_type": relation,
                        "confidence": confidence,
                        "provenance_type": provenance,
                        "claim_id": claim["id"],
                        "document_id": document_id,
                        "explanation": "Relation extracted from the source claim.",
                    })

        return {"relationships": accepted, "accepted": len(accepted), "rejected": rejected}
