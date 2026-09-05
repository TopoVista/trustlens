"""Hybrid Workspace-Scoped Knowledge Retriever (lightweight, no FAISS).

Combines persisted dense chunk embeddings (stored as BLOBs in SQLite) with
keyword entity search and relational graph traversal, keeping strict workspace
isolation.

Chunk embeddings are generated once per chunk (via the configured embedding
service, OpenAI-backed with an offline fallback) and persisted in the
``chunk_embeddings`` table. Only the query is embedded per request; previously
embedded chunks are never re-embedded.
"""
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

    def _ensure_chunk_embeddings(self, workspace_id: str, chunks: List[Dict[str, Any]]) -> np.ndarray:
        """Return the embedding matrix (chunk order) for the given chunks.

        Missing embeddings are computed once (OpenAI-backed, with deterministic
        offline fallback) and persisted to the chunk_embeddings table.
        """
        stored = self.repo.get_chunk_embeddings(workspace_id)
        vectors: Dict[str, np.ndarray] = {}
        pending: List[Dict[str, Any]] = []

        for chunk in chunks:
            chunk_id = chunk["id"]
            if chunk_id in stored:
                vectors[chunk_id] = stored[chunk_id][0]
            else:
                pending.append(chunk)

        if pending:
            model = self._get_model()
            texts = [p.get("text", "") for p in pending]
            new_vectors = model.encode(texts, normalize_embeddings=True).astype(np.float32)
            model_name = model.get_model_name()
            for chunk, vec in zip(pending, new_vectors):
                vec32 = np.asarray(vec, dtype=np.float32)
                self.repo.set_chunk_embedding(
                    workspace_id,
                    chunk["id"],
                    vec32.tobytes(),
                    int(vec32.shape[0]),
                    model_name,
                )
                vectors[chunk["id"]] = vec32
            logger.info(
                "Embedded and persisted %d new chunk vector(s) using '%s'.",
                len(pending),
                model_name,
            )

        matrix = np.vstack([vectors[c["id"]] for c in chunks])
        return matrix.astype(np.float32)

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

        # 1. Semantic vector retrieval (query embedded once, chunks persisted)
        model = self._get_model()
        query_emb = model.encode([query], normalize_embeddings=True)[0].astype(np.float32)
        chunk_embs = self._ensure_chunk_embeddings(workspace_id, chunks)

        # Cosine similarity via inner product (normalized vectors)
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
