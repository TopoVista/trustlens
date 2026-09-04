"""Evidence Specialist for TrustLens"""
from typing import Any, Dict, List
from app.specialists.base import BaseSpecialist
from app.models.nli import verify_claim_batch


class EvidenceAgent(BaseSpecialist):
    """
    Answers: 'Why should I believe this?'
    Locates strongest evidence for claims, checks premise-hypothesis entailment,
    and returns exact passages with location coordinates and support strength.
    """

    def __init__(self):
        super().__init__(
            name="Evidence Specialist",
            description="Evaluates evidentiary support strength and maps claims to exact source passages",
            capabilities=["evidence_retrieval", "evidence_scoring", "citation_mapping"]
        )

    async def analyze(self, workspace_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        claims = context.get("claims", [])
        candidate_chunks = context.get("candidate_chunks", [])

        if not claims or not candidate_chunks:
            return {"verified_claims": []}

        results = []

        for c in claims:
            statement = c.get("statement", "")
            best_support = None
            best_support_score = 0.0
            contradiction_found = None
            contra_score = 0.0

            # Build batch for this claim against all chunks
            valid_chunks = [ch for ch in candidate_chunks if ch.get("text", "").strip()]
            if not valid_chunks:
                results.append({
                    **c,
                    "status": "UNSUPPORTED",
                    "confidence": 0.3,
                    "evidence": []
                })
                continue

            pairs = [(statement, ch.get("text", "")) for ch in valid_chunks]
            try:
                nli_results = verify_claim_batch(pairs)
            except Exception:
                nli_results = [("neutral", 0.5)] * len(valid_chunks)

            for chunk, (label, confidence_score) in zip(valid_chunks, nli_results):
                passage = chunk.get("text", "")
                entail_score = confidence_score if label == "entailment" else 0.0
                contra_score_chunk = confidence_score if label == "contradiction" else 0.0

                if contra_score_chunk >= 0.70 and contra_score_chunk > contra_score:
                    contra_score = contra_score_chunk
                    contradiction_found = {
                        "chunk_id": chunk.get("chunk_id"),
                        "document_id": chunk.get("document_id"),
                        "document_title": chunk.get("document_title", ""),
                        "exact_passage": passage,
                        "location_ref": chunk.get("location_info", ""),
                        "strength": round(contra_score_chunk, 3),
                        "relationship_type": "CONTRADICTS"
                    }

                if entail_score > best_support_score:
                    best_support_score = entail_score
                    best_support = {
                        "chunk_id": chunk.get("chunk_id"),
                        "document_id": chunk.get("document_id"),
                        "document_title": chunk.get("document_title", ""),
                        "exact_passage": passage,
                        "location_ref": chunk.get("location_info", ""),
                        "strength": round(entail_score, 3),
                        "relationship_type": "SUPPORTS"
                    }

            # Determine Claim Status
            if contradiction_found:
                status = "CONTRADICTED"
                final_confidence = contra_score
                evidence_list = [contradiction_found]
                if best_support and best_support_score > 0.5:
                    evidence_list.append(best_support)
            elif best_support_score >= 0.70:
                status = "SUPPORTED"
                final_confidence = best_support_score
                evidence_list = [best_support]
            elif best_support_score >= 0.40:
                status = "PARTIALLY_SUPPORTED"
                final_confidence = best_support_score
                evidence_list = [best_support] if best_support else []
            else:
                status = "UNSUPPORTED"
                final_confidence = 0.3
                evidence_list = []

            results.append({
                **c,
                "status": status,
                "confidence": round(final_confidence, 3),
                "evidence": evidence_list
            })

        return {"verified_claims": results}
