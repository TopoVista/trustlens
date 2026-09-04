"""Contradiction Investigation Specialist for TrustLens"""
import re
from typing import Any, Dict, List
from app.specialists.base import BaseSpecialist


class ContradictionAgent(BaseSpecialist):
    """
    Identifies factual and quantitative conflicts between workspace documents.
    Determines whether discrepancies stem from temporal changes, differing definitions,
    measurement units, or genuine factual contradictions.
    """

    def __init__(self):
        super().__init__(
            name="Contradiction Specialist",
            description="Detects factual conflicts and investigates temporal, semantic, or quantitative causes",
            capabilities=["conflict_detection", "semantic_explanation", "divergence_analysis"]
        )

    async def analyze(self, workspace_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        claims = context.get("claims", [])
        contradictions = []

        # Compare claim pairs for numerical or polarity discrepancies
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                c1 = claims[i]
                c2 = claims[j]

                # Check if claims come from different documents or passages
                if c1.get("document_id") == c2.get("document_id") and c1.get("document_id") is not None:
                    continue

                s1 = c1.get("statement", "")
                s2 = c2.get("statement", "")

                conflict_analysis = self._evaluate_potential_conflict(s1, s2)
                if conflict_analysis["is_conflict"]:
                    contradictions.append({
                        "claim_a": s1,
                        "doc_a": c1.get("document_title", "Document A"),
                        "claim_b": s2,
                        "doc_b": c2.get("document_title", "Document B"),
                        "cause": conflict_analysis["cause"],
                        "explanation": conflict_analysis["explanation"],
                        "severity": conflict_analysis["severity"]
                    })

        return {"contradictions": contradictions, "count": len(contradictions)}

    def _evaluate_potential_conflict(self, text_a: str, text_b: str) -> Dict[str, Any]:
        """Heuristic and pattern check for conflicting figures or statements."""
        # Check for numbers in both statements
        nums_a = re.findall(r"[\$€£]?\d+(?:\.\d+)?(?:%|M|B|k)?", text_a)
        nums_b = re.findall(r"[\$€£]?\d+(?:\.\d+)?(?:%|M|B|k)?", text_b)

        # Check for years/dates
        years_a = re.findall(r"\b(20\d\d)\b", text_a)
        years_b = re.findall(r"\b(20\d\d)\b", text_b)

        # 1. Temporal difference check
        if years_a and years_b and years_a[0] != years_b[0]:
            if nums_a and nums_b and nums_a[0] != nums_b[0]:
                return {
                    "is_conflict": True,
                    "cause": "TEMPORAL_VARIANCE",
                    "severity": "LOW",
                    "explanation": f"Discrepancy likely reflects changes across different time periods ({years_a[0]} vs {years_b[0]}) rather than a factual disagreement."
                }

        # 2. Opposite semantic polarity check
        neg_words = {"not", "never", "declined", "decreased", "dropped", "reduced", "denied", "prohibited"}
        pos_words = {"increased", "grew", "surpassed", "expanded", "permitted", "mandatory", "required"}

        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())

        has_neg_a = bool(words_a & neg_words)
        has_pos_a = bool(words_a & pos_words)
        has_neg_b = bool(words_b & neg_words)
        has_pos_b = bool(words_b & pos_words)

        if (has_neg_a and has_pos_b) or (has_pos_a and has_neg_b):
            # Check for topic overlap
            common_words = (words_a & words_b) - neg_words - pos_words
            meaningful_overlap = [w for w in common_words if len(w) > 4]
            if len(meaningful_overlap) >= 2:
                return {
                    "is_conflict": True,
                    "cause": "OPPOSITE_CONCLUSIONS",
                    "severity": "HIGH",
                    "explanation": f"Documents express conflicting conclusions regarding common concepts: {', '.join(meaningful_overlap[:3])}."
                }

        # 3. Direct metric divergence in same temporal context
        if nums_a and nums_b and nums_a[0] != nums_b[0]:
            common_words = (words_a & words_b)
            topic_overlap = [w for w in common_words if len(w) > 4]
            if len(topic_overlap) >= 2:
                return {
                    "is_conflict": True,
                    "cause": "METRIC_DIVERGENCE",
                    "severity": "HIGH",
                    "explanation": f"Different values reported ({nums_a[0]} vs {nums_b[0]}) for shared subject: {', '.join(topic_overlap[:3])}."
                }

        return {"is_conflict": False, "cause": "NONE", "severity": "NONE", "explanation": ""}
