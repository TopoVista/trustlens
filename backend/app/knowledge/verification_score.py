"""Interpretable evidence-support scoring; deliberately not a truth probability."""
from __future__ import annotations

from typing import Any, Dict


_AUTHORITY = {"HIGH": 0.95, "OFFICIAL": 0.95, "MEDIUM": 0.72, "LOW": 0.45, "UNVERIFIED": 0.35}


def compute_support_score(authority: str, relevance: float, nli_confidence: float,
                          numeric: Dict[str, Any], temporal: Dict[str, Any],
                          supporting_sources: int, contradicting_sources: int) -> Dict[str, Any]:
    """Combine transparent evidence signals into a 0-100 support score."""
    authority_score = _AUTHORITY.get((authority or "MEDIUM").upper(), 0.72)
    relevance_score = max(0.0, min(1.0, float(relevance or 0.0)))
    nli_score = max(0.0, min(1.0, float(nli_confidence or 0.0)))
    numeric_score = numeric.get("confidence") if numeric.get("confidence") is not None else nli_score
    temporal_score = temporal.get("confidence") if temporal.get("confidence") is not None else nli_score
    source_total = supporting_sources + contradicting_sources
    agreement = supporting_sources / source_total if source_total else 0.0
    score = (0.20 * authority_score + 0.20 * relevance_score + 0.30 * nli_score +
             0.12 * numeric_score + 0.08 * temporal_score + 0.10 * agreement)
    return {
        "score": round(max(0.0, min(100.0, score * 100)), 1),
        "components": {
            "source_authority": round(authority_score * 100, 1),
            "evidence_relevance": round(relevance_score * 100, 1),
            "nli_support": round(nli_score * 100, 1),
            "numeric_consistency": round(numeric_score * 100, 1),
            "temporal_consistency": round(temporal_score * 100, 1),
            "cross_source_agreement": round(agreement * 100, 1),
        },
        "meaning": "Evidence support score, not an objective truth probability.",
    }
