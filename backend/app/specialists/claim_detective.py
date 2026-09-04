"""Claim Detective Specialist for TrustLens"""
import re
from typing import Any, Dict, List
from app.specialists.base import BaseSpecialist
from app.pipeline.claims import split_into_claims, normalize_claim


class ClaimDetective(BaseSpecialist):
    """
    Extracts meaningful factual assertions from text, normalizes statements,
    identifies duplicate claims, and connects claims to entities.
    """

    def __init__(self):
        super().__init__(
            name="Claim Detective",
            description="Extracts and normalizes atomic factual claims with confidence estimation",
            capabilities=["claim_extraction", "claim_normalization", "deduplication"]
        )

    async def analyze(self, workspace_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        text = context.get("text", "")
        doc_id = context.get("document_id")

        if not text.strip():
            return {"claims": []}

        # Use conservative claim splitting
        raw_statements = split_into_claims(text)
        claims = []
        seen = set()

        for s in raw_statements:
            cleaned = s.strip()
            if len(cleaned) < 15:
                continue

            normalized = normalize_claim(cleaned)
            norm_key = normalized.lower()
            if norm_key in seen:
                continue
            seen.add(norm_key)

            # Classify claim type
            claim_type = "METRIC" if any(char.isdigit() or char in "$%€" for char in cleaned) else "FACTUAL"

            claims.append({
                "statement": cleaned,
                "normalized_statement": normalized,
                "claim_type": claim_type,
                "document_id": doc_id,
                "workspace_id": workspace_id,
                "status": "UNRESOLVED",
                "confidence": 0.85 if claim_type == "METRIC" else 0.75
            })

        return {"claims": claims, "count": len(claims)}
