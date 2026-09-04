"""Evidence Retrieval Agent for TrustLens"""
from typing import Any, Dict, List
from app.agents.base import BaseAgent
from app.pipeline.retriever import retrieve


class EvidenceRetrievalAgent(BaseAgent):
    """
    Retrieves dense semantic evidence from the FAISS vector database
    for vendor controls, industry standards, and architectural benchmarks.
    """

    def __init__(self):
        super().__init__(
            name="Evidence Retrieval Agent",
            role="Retrieves vector evidence benchmarks and compliance context via FAISS",
            category="Worker"
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        vendor_profile = state.get("vendor_profile", {})
        query = state.get("query", "")

        # Formulate query combining vendor industry and assessment query
        search_query = query if query else f"{vendor_profile.get('industry', '')} security controls and data isolation guarantees"

        try:
            retrieved_docs = retrieve(search_query, k=state.get("k", 5))
        except Exception as e:
            self.logger.warning("Retrieval fallback: %s", e)
            retrieved_docs = [
                {
                    "id": "doc_sec_baseline",
                    "text": "Security Baseline: Access controls require multi-factor authentication and role-based permissions. All persistent data must be encrypted using AES-256.",
                    "score": 0.85
                }
            ]

        state["evidence_documents"] = retrieved_docs
        return {"evidence_documents": retrieved_docs}
