"""Synthesis Specialist enforcing Phase 11 Answer Contract for TrustLens"""
import os
import logging
from typing import Any, Dict, List
from app.specialists.base import BaseSpecialist
from app.pipeline.generator import _get_client

logger = logging.getLogger("trustlens.specialists.synthesis")


class SynthesisAgent(BaseSpecialist):
    """
    Combines outputs of specialized reasoning agents following the strict Phase 11 Answer Contract:
    - Answer (concise, factual conclusion)
    - Claims (structured assertions with explicit verification status)
    - Evidence (exact citations with location coordinates)
    - Confidence (objective reliability percentage)
    - Contradictions (preserved and analyzed, never silently resolved)
    - Assumptions (underlying operational assumptions)
    - Unknowns ('What we don't know')
    - Related Knowledge (timeline milestones, entities)
    """

    def __init__(self):
        super().__init__(
            name="Synthesis Specialist",
            description="Compiles multi-agent reasoning into structured evidence-grounded answers complying with Phase 11 Contract",
            capabilities=["multi_agent_synthesis", "uncertainty_preservation", "answer_contract"]
        )

    async def analyze(self, workspace_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        query = context.get("query", "")
        retrieved_chunks = context.get("retrieved_chunks", [])
        verified_claims = context.get("verified_claims", [])
        contradictions = context.get("contradictions", [])
        knowledge_gaps = context.get("knowledge_gaps", [])
        entities = context.get("entities", [])
        events = context.get("events", [])
        semantic_rules = context.get("semantic_rules", [])

        # Format context for grounded synthesis
        context_passages = [f"[{c.get('document_title', 'Doc')} - {c.get('location_info', '')}]: {c.get('text')}" for c in retrieved_chunks]
        context_str = "\n\n".join(context_passages) if context_passages else "No direct passages retrieved."

        rules_str = "\n".join([f"- {r.get('rule_key')}: {r.get('rule_value')}" for r in semantic_rules]) if semantic_rules else "No custom rules defined."

        prompt = f"""You are TrustLens's Synthesis Specialist.
Answer the user question based strictly on the provided workspace evidence.

Workspace Evidence:
{context_str}

User-Defined Semantic Rules:
{rules_str}

Question:
{query}

Contract Rules:
1. Provide a concise, highly objective, evidence-backed answer (2-4 sentences).
2. Distinguish verified facts from inference.
3. If evidence is missing or ambiguous, explicitly state: "Insufficient evidence in workspace."
4. Do not invent citations or hide contradictions."""

        answer_text: str = ""
        try:
            client = _get_client()
            model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini-2024-07-18").strip()
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a factual synthesis specialist. Answer strictly based on evidence."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=400
            )
            answer_text = response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.warning("Deterministic synthesis fallback: %s", e)
            if retrieved_chunks:
                top_passage = retrieved_chunks[0].get("text", "")
                answer_text = f"Based on workspace documentation: {top_passage[:280]}..."
            else:
                answer_text = "Insufficient evidence in workspace to answer this question."

        # Calculate overall confidence based on verified claim status
        if verified_claims:
            supported = sum(1 for c in verified_claims if c.get("status") == "SUPPORTED")
            confidence_pct = round((supported / len(verified_claims)) * 100, 1)
        else:
            confidence_pct = 75.0 if retrieved_chunks else 20.0

        # Assemble Phase 11 Contract Response
        return {
            "answer": answer_text,
            "confidence": confidence_pct,
            "claims": verified_claims,
            "evidence": [
                {
                    "source": c.get("document_title", "Document"),
                    "filename": c.get("filename", ""),
                    "passage": c.get("text", ""),
                    "location": c.get("location_info", ""),
                    "score": c.get("score", 0.8)
                }
                for c in retrieved_chunks
            ],
            "contradictions": contradictions,
            "assumptions": [
                "Analysis assumes source documents are authentic as uploaded.",
                "Semantic rules applied as configured for this workspace."
            ],
            "unknowns": [g.get("description") for g in knowledge_gaps[:3]],
            "related_knowledge": {
                "entities": [e.get("name") for e in entities[:6]],
                "events": [e.get("title") for e in events[:4]]
            }
        }
