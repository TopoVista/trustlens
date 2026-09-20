"""Deterministic temporal validation with explicit update-aware semantics."""
from __future__ import annotations

import re
from typing import Any, Dict


_DATE = re.compile(r"\b(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}(?:,?\s+\d{4})?|(?:19|20)\d{2})\b", re.IGNORECASE)
_UPDATE = re.compile(r"\b(postponed|rescheduled|revised|updated|cancelled|formerly|previously|effective from)\b", re.IGNORECASE)


def verify_temporal_claim(claim: str, evidence: str) -> Dict[str, Any]:
    claim_dates = _DATE.findall(claim or "")
    evidence_dates = _DATE.findall(evidence or "")
    if not claim_dates or not evidence_dates:
        return {"status": "NOT_APPLICABLE", "confidence": None, "explanation": "No comparable explicit date was found."}
    if set(date.lower() for date in claim_dates) & set(date.lower() for date in evidence_dates):
        return {"status": "TEMPORALLY_CONSISTENT", "confidence": 1.0, "explanation": "Claim and evidence share an explicit date."}
    if _UPDATE.search(evidence or ""):
        return {"status": "UPDATED_BY", "confidence": 0.85,
                "explanation": "Evidence gives a different date with an explicit update/reschedule modifier."}
    return {"status": "TEMPORAL_CONFLICT", "confidence": 0.0,
            "explanation": "Claim and evidence contain different dates without an explicit update modifier."}
