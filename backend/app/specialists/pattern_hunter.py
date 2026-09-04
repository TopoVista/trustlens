"""Pattern Hunter Specialist for TrustLens"""
import re
from typing import Any, Dict, List
from collections import Counter
from app.specialists.base import BaseSpecialist


class PatternHunter(BaseSpecialist):
    """
    Finds non-obvious patterns, emerging trends, anomalies, and recurring clusters
    across multiple documents without requiring an explicit user prompt.
    """

    def __init__(self):
        super().__init__(
            name="Pattern Hunter",
            description="Discovers recurring patterns, anomalies, and multi-document clusters with supporting evidence",
            capabilities=["trend_discovery", "anomaly_detection", "pattern_clustering"]
        )

    async def analyze(self, workspace_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        chunks = context.get("chunks", [])
        claims = context.get("claims", [])

        if not chunks and not claims:
            return {"patterns": []}

        patterns = []

        # 1. Topic clustering over all chunks
        all_words = []
        stop_words = {"this", "that", "with", "from", "have", "were", "been", "their", "which", "about", "there", "would"}
        for c in chunks:
            words = re.findall(r"\b[a-z]{5,}\b", c.get("text", "").lower())
            all_words.extend([w for w in words if w not in stop_words])

        counts = Counter(all_words)
        common = counts.most_common(4)

        for word, freq in common:
            if freq >= 3:
                # Find matching chunks for evidence
                matching_chunks = [c for c in chunks if word in c.get("text", "").lower()][:3]
                doc_titles = list(set([c.get("document_title", "Document") for c in matching_chunks]))
                if len(doc_titles) >= 2:
                    patterns.append({
                        "pattern_type": "CROSS_DOCUMENT_THEME",
                        "title": f"Recurring Theme: '{word.capitalize()}'",
                        "description": f"The concept '{word}' appears consistently across {len(doc_titles)} distinct sources: {', '.join(doc_titles)}.",
                        "confidence": 0.88,
                        "evidence": [c.get("text")[:140] + "..." for c in matching_chunks]
                    })

        # 2. Percentage and growth trend patterns
        growth_claims = [c for c in claims if "%" in c.get("statement", "") or "increase" in c.get("statement", "").lower()]
        if len(growth_claims) >= 2:
            patterns.append({
                "pattern_type": "GROWTH_METRIC_CLUSTER",
                "title": "Positive Growth Trajectory Assertions",
                "description": f"Identified {len(growth_claims)} separate statements highlighting positive growth or performance gains.",
                "confidence": 0.82,
                "evidence": [c.get("statement") for c in growth_claims[:3]]
            })

        return {"patterns": patterns, "pattern_count": len(patterns)}
