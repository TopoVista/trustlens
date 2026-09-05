"""Build and persist corpus embeddings for the TrustLens knowledge base.

Embeds every document in backend/data/processed_docs/docs.json using the OpenAI
Embeddings API (OPENAI_EMBEDDING_MODEL, default text-embedding-3-small) and
stores the vectors in backend/data/corpus_embeddings.npy.

Run once before deployment (or whenever the corpus changes):

    cd backend
    python scripts/build_corpus_embeddings.py

This keeps the first retrieval request fast in production: the persisted
vectors are loaded instead of recomputed. If OPENAI_API_KEY is not configured,
the script still succeeds using deterministic offline fallback embeddings.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.embeddings import build_index  # noqa: E402


if __name__ == "__main__":
    count = build_index()
    print(f"Persisted embeddings for {count} corpus documents.")