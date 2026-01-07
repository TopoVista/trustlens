"verified answer assembler"

from typing import List, Dict
from app.pipeline.claims import split_into_claims, normalize_claim
from app.pipeline.verifier import verify_single_claim


LABEL_TO_COLOR = {
    "SUPPORTED": "green",
    "NOT_SUPPORTED": "yellow",
    "CONTRADICTED": "red"
}


def assemble_verified_answer(answer_text: str, k: int = 5) -> List[Dict]:
    """
    Break an answer into claims, verify each claim, and attach labels + colors.

    Returns:
        [
            {
                "claim": str,
                "label": str,
                "score": float,
                "color": str
            }
        ]
    """
    claims = split_into_claims(answer_text)

    verified = []

    for raw_claim in claims:
        normalized = normalize_claim(raw_claim)
        result = verify_single_claim(normalized, k=k)

        verified.append({
            "claim": raw_claim,
            "label": result["label"],
            "score": round(result["score"], 3),
            "color": LABEL_TO_COLOR[result["label"]]
        })

    return verified
