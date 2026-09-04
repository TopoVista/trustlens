"""Knowledge Gap Specialist for TrustLens"""
from typing import Any, Dict, List
from app.specialists.base import BaseSpecialist


class KnowledgeGapAgent(BaseSpecialist):
    """
    Answers: 'What don't we know?'
    Identifies unsupported strategic assumptions, missing metrics, unresolved contradictions,
    and missing evidence within the workspace.
    """

    def __init__(self):
        super().__init__(
            name="Knowledge Gap Specialist",
            description="Identifies blind spots, unbacked claims, missing metrics, and unresolved contradictions",
            capabilities=["gap_detection", "missing_metrics", "assumption_auditing"]
        )

    async def analyze(self, workspace_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        claims = context.get("claims", [])
        contradictions = context.get("contradictions", [])
        events = context.get("events", [])

        gaps: List[Dict[str, Any]] = []

        # 1. Unsupported or unbacked claims
        for c in claims:
            if c.get("status") in {"UNSUPPORTED", "UNRESOLVED"}:
                gaps.append({
                    "type": "UNSUPPORTED_CLAIM",
                    "title": "Unverified Statement",
                    "description": f"Statement lacks direct evidence in workspace: \"{c.get('statement')}\"",
                    "impact": "High if used in strategic decision making",
                    "recommendation": "Upload primary source documentation or attestation."
                })

        # 2. Unresolved contradictions
        for contra in contradictions:
            gaps.append({
                "type": "UNRESOLVED_CONTRADICTION",
                "title": f"Conflicting Data on {contra.get('cause')}",
                "description": f"Divergence between {contra.get('doc_a')} and {contra.get('doc_b')}: {contra.get('explanation')}",
                "impact": "Medium to High",
                "recommendation": "Determine authoritative source or review temporal context."
            })

        # 3. Missing temporal continuity
        if len(events) >= 2:
            years = [int(e.get("timestamp_val", 0)) for e in events if e.get("timestamp_val", 0) > 1900]
            if years:
                min_yr = min(years)
                max_yr = max(years)
                present_years = set(years)
                for yr in range(min_yr, max_yr):
                    if yr not in present_years and (max_yr - min_yr) <= 10:
                        gaps.append({
                            "type": "TIMELINE_GAP",
                            "title": f"Missing Historical Period ({yr})",
                            "description": f"No milestones or records indexed for year {yr} between {min_yr} and {max_yr}.",
                            "impact": "Low",
                            "recommendation": f"Add reports or documentation covering {yr} operations."
                        })

        return {"knowledge_gaps": gaps, "gap_count": len(gaps)}
