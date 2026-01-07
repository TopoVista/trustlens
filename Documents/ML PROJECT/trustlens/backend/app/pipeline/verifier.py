"""Verifier"""
from typing import List, Dict
from app.models.nli import verify_claim
from app.pipeline.retriever import retrieve_for_claim


ENTAILMENT_THRESHOLD = 0.7
CONTRADICTION_THRESHOLD = 0.7


def verify_single_claim(claim: str, k: int = 5) -> Dict:
    """
    Verify a single normalized claim against multiple evidence documents.

    Returns:
        {
            "claim": str,
            "label": "SUPPORTED" | "CONTRADICTED" | "NOT_SUPPORTED",
            "score": float
        }
    """
    evidence_docs = retrieve_for_claim(claim, k=k)

    entailment_scores = []
    contradiction_scores = []

    for doc in evidence_docs:
        label, confidence = verify_claim(claim, doc["text"])

        if label == "entailment":
            entailment_scores.append(confidence)
        elif label == "contradiction":
            contradiction_scores.append(confidence)

    # Decision logic
    if contradiction_scores and max(contradiction_scores) >= CONTRADICTION_THRESHOLD:
        return {
            "claim": claim,
            "label": "CONTRADICTED",
            "score": max(contradiction_scores)
        }

    if entailment_scores and max(entailment_scores) >= ENTAILMENT_THRESHOLD:
        return {
            "claim": claim,
            "label": "SUPPORTED",
            "score": max(entailment_scores)
        }

    return {
        "claim": claim,
        "label": "NOT_SUPPORTED",
        "score": max(entailment_scores + contradiction_scores, default=0.0)
    }
