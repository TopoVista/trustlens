"""Deterministic numeric validation used alongside semantic NLI."""
from __future__ import annotations

import re
from typing import Any, Dict


_PERCENT = re.compile(r"(-?\d+(?:\.\d+)?)\s*%")
_FROM_TO = re.compile(r"(?:from\s+)?[$€£]?\s*(-?\d+(?:\.\d+)?)\s*(?:m|b|k)?\s+(?:to|->|–|—)\s+[$€£]?\s*(-?\d+(?:\.\d+)?)", re.IGNORECASE)


def verify_numeric_claim(claim: str, evidence: str) -> Dict[str, Any]:
    """Verify explicit percentage-change claims from source values where possible."""
    claim_percent = _PERCENT.search(claim or "")
    values = _FROM_TO.search(evidence or "")
    if not claim_percent:
        return {"status": "NOT_APPLICABLE", "confidence": None, "explanation": "Claim has no explicit percentage to calculate."}
    expected = float(claim_percent.group(1))
    if values:
        start, end = float(values.group(1)), float(values.group(2))
        if start == 0:
            return {"status": "NOT_APPLICABLE", "confidence": None, "explanation": "Percentage change is undefined from a zero baseline."}
        observed = round(((end - start) / abs(start)) * 100, 2)
        if abs(observed - expected) <= 0.5:
            return {"status": "NUMERICALLY_VERIFIED", "confidence": 1.0, "observed": observed,
                    "explanation": f"Calculated ({end} - {start}) / {start} = {observed}% matches the claim."}
        return {"status": "NUMERIC_CONFLICT", "confidence": 0.0, "observed": observed,
                "explanation": f"Calculated change is {observed}%, not the claimed {expected}%."}
    evidence_percent = _PERCENT.search(evidence or "")
    if evidence_percent:
        observed = float(evidence_percent.group(1))
        if abs(observed - expected) <= 0.1:
            return {"status": "NUMERICALLY_VERIFIED", "confidence": 0.9, "observed": observed,
                    "explanation": "The evidence states the same percentage."}
        return {"status": "NUMERIC_CONFLICT", "confidence": 0.0, "observed": observed,
                "explanation": f"Evidence reports {observed}% rather than {expected}%."}
    return {"status": "NOT_APPLICABLE", "confidence": None, "explanation": "Evidence does not expose a comparable numeric value."}
