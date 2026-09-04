"""Evaluation metrics: faithfulness, hallucination rate, and claim precision"""
from typing import List, Dict


def hallucination_rate(verified_claims: List[Dict]) -> float:
    """
    Fraction of claims that could not be grounded in evidence
    (either NOT_SUPPORTED or CONTRADICTED).
    Returns 0.0 if no claims exist.
    """
    if not verified_claims:
        return 0.0

    unverified = sum(
        1 for c in verified_claims
        if c.get("label") in {"NOT_SUPPORTED", "CONTRADICTED"}
    )
    return round(unverified / len(verified_claims), 3)


def claim_precision(verified_claims: List[Dict]) -> float:
    """
    Fraction of claims that are strictly SUPPORTED.
    Returns 0.0 if no claims exist.
    """
    if not verified_claims:
        return 0.0

    supported = sum(
        1 for c in verified_claims
        if c.get("label") == "SUPPORTED"
    )
    return round(supported / len(verified_claims), 3)


def faithfulness(verified_claims: List[Dict]) -> float:
    """
    Confidence-weighted faithfulness score across all claims:
    (Sum of confidence scores of SUPPORTED claims) / (Total number of claims).
    Guaranteed safe against division by zero (returns 0.0 on empty claims).
    """
    if not verified_claims:
        return 0.0

    support_sum = sum(
        c.get("score", 0.0) for c in verified_claims
        if c.get("label") == "SUPPORTED"
    )
    return round(support_sum / len(verified_claims), 3)


def compute_summary_stats(verified_claims: List[Dict]) -> Dict:
    """
    Generate complete summary breakdown dictionary.
    """
    total = len(verified_claims)
    supported = sum(1 for c in verified_claims if c.get("label") == "SUPPORTED")
    not_supported = sum(1 for c in verified_claims if c.get("label") == "NOT_SUPPORTED")
    contradicted = sum(1 for c in verified_claims if c.get("label") == "CONTRADICTED")

    return {
        "claim_count": total,
        "supported": supported,
        "not_supported": not_supported,
        "contradicted": contradicted,
        "faithfulness": faithfulness(verified_claims),
        "hallucination_rate": hallucination_rate(verified_claims)
    }
