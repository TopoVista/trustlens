"""Verified answer assembler: joins decomposition, verification, and visual color assignments"""
import logging
from typing import List, Dict
from app.pipeline.claims import split_into_claims, normalize_claim
from app.pipeline.verifier import verify_single_claim

logger = logging.getLogger("trustlens.assembler")

LABEL_TO_COLOR = {
    "SUPPORTED": "green",
    "NOT_SUPPORTED": "amber",
    "CONTRADICTED": "red"
}


def assemble_verified_answer(answer_text: str, claim_k: int = 3) -> List[Dict]:
    """
    Decompose answer into claims, verify each against independent evidence,
    and attach verification labels, confidence scores, evidence snippets, and UI colors.
    """
    raw_claims = split_into_claims(answer_text)
    if not raw_claims:
        logger.info("No discrete claims extracted from answer.")
        return []

    verified_claims = []
    for raw in raw_claims:
        normalized = normalize_claim(raw)
        result = verify_single_claim(normalized, k=claim_k)

        verified_claims.append({
            "claim": raw,
            "label": result["label"],
            "score": result["score"],
            "color": LABEL_TO_COLOR.get(result["label"], "amber"),
            "evidence": result.get("evidence", [])
        })

    logger.info("Assembled %d verified claims", len(verified_claims))
    return verified_claims
