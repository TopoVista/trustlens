"""Evidence Specialist for TrustLens"""
from typing import Any, Dict, List
from app.specialists.base import BaseSpecialist
from app.models.nli import verify_claim_batch_detailed
from app.specialists.numeric_verifier import verify_numeric_claim
from app.specialists.temporal_verifier import verify_temporal_claim
from app.knowledge.verification_score import compute_support_score


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

            # Compact deterministic reranking prevents every retrieved passage
            # from becoming an NLI pair. Semantic retrieval supplied the pool;
            # lexical overlap and original rank select the best three candidates.
            valid_chunks = [ch for ch in candidate_chunks if ch.get("text", "").strip()]
            if not valid_chunks:
                results.append({
                    **c,
                    "status": "UNSUPPORTED",
                    "confidence": 0.3,
                    "evidence": []
                })
                continue

            claim_tokens = set(statement.lower().split())
            def candidate_rank(chunk):
                overlap = len(claim_tokens & set(chunk.get("text", "").lower().split())) / max(1, len(claim_tokens))
                return float(chunk.get("score", 0.0)) + overlap * 0.2
            valid_chunks = sorted(valid_chunks, key=candidate_rank, reverse=True)[:3]
            pairs = [(statement, ch.get("text", "")) for ch in valid_chunks]
            try:
                nli_results = verify_claim_batch_detailed(pairs)
            except Exception:
                nli_results = [{"label": "neutral", "confidence": 0.5, "method": "NLI", "provider": "deterministic", "model": "lexical-v1", "fallback": True}] * len(valid_chunks)

            supporting_evidence = []
            contradicting_evidence = []
            validation_records = []
            for chunk, nli in zip(valid_chunks, nli_results):
                label = nli["label"]
                confidence_score = nli["confidence"]
                passage = chunk.get("text", "")
                numeric = verify_numeric_claim(statement, passage)
                temporal = verify_temporal_claim(statement, passage)
                validation_records.append({"chunk_id": chunk.get("chunk_id"), "numeric": numeric, "temporal": temporal, "nli": nli})
                entail_score = confidence_score if label == "entailment" else 0.0
                contra_score_chunk = confidence_score if label == "contradiction" else 0.0
                if numeric.get("status") == "NUMERIC_CONFLICT" or temporal.get("status") == "TEMPORAL_CONFLICT":
                    contra_score_chunk = max(contra_score_chunk, 0.9 if numeric.get("status") == "NUMERIC_CONFLICT" else 0.75)

                if contra_score_chunk >= 0.70 and contra_score_chunk > contra_score:
                    contra_score = contra_score_chunk
                    contradiction_found = {
                        "chunk_id": chunk.get("chunk_id"),
                        "document_id": chunk.get("document_id"),
                        "document_title": chunk.get("document_title", ""),
                        "authority_level": chunk.get("authority_level", "MEDIUM"),
                        "exact_passage": passage,
                        "location_ref": chunk.get("location_info", ""),
                        "strength": round(contra_score_chunk, 3),
                        "relationship_type": "CONTRADICTS",
                        "verification_provenance": nli,
                        "numeric_validation": numeric,
                        "temporal_validation": temporal,
                    }
                    contradicting_evidence.append(contradiction_found)

                if entail_score > best_support_score:
                    best_support_score = entail_score
                    best_support = {
                        "chunk_id": chunk.get("chunk_id"),
                        "document_id": chunk.get("document_id"),
                        "document_title": chunk.get("document_title", ""),
                        "authority_level": chunk.get("authority_level", "MEDIUM"),
                        "exact_passage": passage,
                        "location_ref": chunk.get("location_info", ""),
                        "strength": round(entail_score, 3),
                        "relationship_type": "SUPPORTS",
                        "verification_provenance": nli,
                        "numeric_validation": numeric,
                        "temporal_validation": temporal,
                    }
                    supporting_evidence.append(best_support)

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

            numeric_validation = next((item["numeric"] for item in validation_records if item["numeric"].get("status") != "NOT_APPLICABLE"), {"status": "NOT_APPLICABLE"})
            temporal_validation = next((item["temporal"] for item in validation_records if item["temporal"].get("status") != "NOT_APPLICABLE"), {"status": "NOT_APPLICABLE"})
            strongest = best_support or contradiction_found or {}
            support_score = compute_support_score(
                strongest.get("authority_level", "MEDIUM"), strongest.get("strength", 0.0), final_confidence,
                numeric_validation, temporal_validation,
                len({item.get("document_id") for item in supporting_evidence if item.get("document_id")} ),
                len({item.get("document_id") for item in contradicting_evidence if item.get("document_id")} ),
            )
            results.append({
                **c,
                "status": status,
                "confidence": round(final_confidence, 3),
                "evidence": evidence_list,
                "supporting_sources": len({item.get("document_id") for item in supporting_evidence if item.get("document_id")}),
                "contradicting_sources": len({item.get("document_id") for item in contradicting_evidence if item.get("document_id")}),
                "numeric_validation": numeric_validation,
                "temporal_validation": temporal_validation,
                "verification_provenance": [item["nli"] for item in validation_records],
                "trust_support": support_score,
            })

        return {"verified_claims": results}
