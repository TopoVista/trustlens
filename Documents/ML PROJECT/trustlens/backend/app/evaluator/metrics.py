from typing import List, Dict


def hallucination_rate(verified_claims: List[Dict]) -> float:
    """
    Fraction of claims that are hallucinated
    (NOT_SUPPORTED or CONTRADICTED).
    """
    if not verified_claims:
        return 0.0

    hallucinated = sum(
        1 for c in verified_claims
        if c["label"] in {"NOT_SUPPORTED", "CONTRADICTED"}
    )

    return hallucinated / len(verified_claims)


def claim_precision(verified_claims: List[Dict]) -> float:
    """
    Fraction of claims that are supported.
    """
    if not verified_claims:
        return 0.0

    supported = sum(
        1 for c in verified_claims
        if c["label"] == "SUPPORTED"
    )

    return supported / len(verified_claims)


def faithfulness(verified_claims: List[Dict]) -> float:
    """
    Confidence-weighted support score.
    """
    if not verified_claims:
        return 0.0

    support_confidence = sum(
        c["score"] for c in verified_claims
        if c["label"] == "SUPPORTED"
    )

    return support_confidence / len(verified_claims)
