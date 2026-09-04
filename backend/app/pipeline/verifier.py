"""Claim verification engine using NLI and strict decision hierarchy"""
import os
import logging
from typing import List, Dict, Optional
from app.models.nli import verify_claim_batch
from app.pipeline.retriever import retrieve_for_claim

logger = logging.getLogger("trustlens.verifier")

DEFAULT_NLI_THRESHOLD = float(os.getenv("NLI_THRESHOLD", "0.70"))
DEFAULT_CLAIM_RETRIEVAL_K = int(os.getenv("CLAIM_RETRIEVAL_K", "3"))


def verify_single_claim(
    claim: str,
    k: Optional[int] = None,
    threshold: Optional[float] = None
) -> Dict:
    """
    Verify a single claim against independently retrieved evidence documents.

    Returns:
        {
            "claim": str,
            "label": "SUPPORTED" | "CONTRADICTED" | "NOT_SUPPORTED",
            "score": float,
            "evidence": List[Dict]
        }
    """
    retrieval_limit = k if k is not None else DEFAULT_CLAIM_RETRIEVAL_K
    active_threshold = threshold if threshold is not None else DEFAULT_NLI_THRESHOLD

    evidence_docs = retrieve_for_claim(claim, k=retrieval_limit)

    if not evidence_docs:
        return {
            "claim": claim,
            "label": "NOT_SUPPORTED",
            "score": 0.0,
            "evidence": []
        }

    # Batch evaluate NLI across all candidate evidence docs for this claim
    pairs = [(claim, doc["text"]) for doc in evidence_docs]
    nli_results = verify_claim_batch(pairs)

    entailment_scores = []
    contradiction_scores = []

    for (label, confidence) in nli_results:
        if label == "contradiction":
            contradiction_scores.append(confidence)
        elif label == "entailment":
            entailment_scores.append(confidence)

    # Strict Decision Hierarchy:
    # 1. Strong contradiction overrides entailment
    # 2. Strong entailment confirms support
    # 3. Everything else is NOT_SUPPORTED (insufficient evidence)
    if contradiction_scores and max(contradiction_scores) >= active_threshold:
        verdict = "CONTRADICTED"
        final_score = max(contradiction_scores)
    elif entailment_scores and max(entailment_scores) >= active_threshold:
        verdict = "SUPPORTED"
        final_score = max(entailment_scores)
    else:
        verdict = "NOT_SUPPORTED"
        all_scores = entailment_scores + contradiction_scores
        final_score = max(all_scores) if all_scores else 0.0

    return {
        "claim": claim,
        "label": verdict,
        "score": round(float(final_score), 3),
        "evidence": [
            {
                "id": doc["id"],
                "text": doc["text"],
                "score": doc["score"]
            }
            for doc in evidence_docs
        ]
    }
