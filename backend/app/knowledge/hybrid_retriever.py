"""Hybrid Workspace-Scoped Knowledge Retriever combining Dense Vectors and Relational Graph"""
import logging
from typing import Any, Dict, List, Optional
import numpy as np
from app.knowledge.repository import KnowledgeRepository
from app.models.embeddings import get_embedding_model

logger = logging.getLogger("trustlens.knowledge.retriever")


class HybridKnowledgeRetriever:
    """
    Combines dense semantic vector retrieval, keyword entity search,
    and relational graph traversal with strict workspace isolation.
    """

    def __init__(self, repo: Optional[KnowledgeRepository] = None):
        self.repo = repo or KnowledgeRepository()
        self._model = None

    def _get_model(self):
        if self._model is None:
            self._model = get_embedding_model()
        return self._model

    def retrieve(
        self,
        workspace_id: str,
        query: str,
        k: int = 5,
        apply_authority_weighting: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval over workspace chunks, entities, and evidence.
        Strictly scopes all lookups to workspace_id.
        """
        chunks = self.repo.get_chunks(workspace_id)
        if not chunks:
            return []

        # 1. Semantic Embedding Retrieval
        model = self._get_model()
        query_emb = model.encode([query], normalize_embeddings=True)[0]
        
        chunk_texts = [c["text"] for c in chunks]
        chunk_embs = model.encode(chunk_texts, normalize_embeddings=True)

        # Cosine similarity inner product
        sim_scores = np.dot(chunk_embs, query_emb)

        # 2. Authority Level Weighting & Keyword Matching
        docs_map = {d["id"]: d for d in self.repo.get_documents(workspace_id)}
        query_terms = set(query.lower().split())

        scored_chunks = []
        for idx, chunk in enumerate(chunks):
            base_score = float(sim_scores[idx])
            doc = docs_map.get(chunk["document_id"], {})
            authority = doc.get("authority_level", "MEDIUM")

            # Keyword overlap boost
            chunk_lower = chunk["text"].lower()
            overlap = sum(1 for term in query_terms if len(term) > 3 and term in chunk_lower)
            keyword_boost = min(0.15, overlap * 0.03)

            final_score = base_score + keyword_boost

            if apply_authority_weighting:
                if authority == "HIGH":
                    final_score *= 1.15
                elif authority == "LOW":
                    final_score *= 0.85

            scored_chunks.append({
                "chunk_id": chunk["id"],
                "document_id": chunk["document_id"],
                "document_title": doc.get("title", "Untitled"),
                "filename": doc.get("filename", ""),
                "authority_level": authority,
                "text": chunk["text"],
                "location_info": chunk.get("location_info", ""),
                "score": round(final_score, 4)
            })

        # Rank by final score descending
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:k]

    def retrieve_entity_context(self, workspace_id: str, query: str) -> List[Dict[str, Any]]:
        """Finds entities mentioned in the query and returns their graph connections."""
        entities = self.repo.get_entities(workspace_id)
        matched_entities = []
        query_lower = query.lower()

        for ent in entities:
            if ent["normalized_name"] in query_lower or any(alias.lower() in query_lower for alias in ent.get("aliases", [])):
                matched_entities.append(ent)

        return matched_entities
