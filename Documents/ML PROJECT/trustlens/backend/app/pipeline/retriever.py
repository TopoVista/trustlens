"""Retriever"""

import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_PATH = "backend/data/index.faiss"
DOC_STORE_PATH = "backend/data/doc_store.json"

_model = None
_index = None
_docs = None


def _load_resources():
    global _model, _index, _docs

    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")

    if _index is None:
        _index = faiss.read_index(INDEX_PATH)

    if _docs is None:
        with open(DOC_STORE_PATH, "r", encoding="utf-8") as f:
            _docs = json.load(f)


def retrieve(query, k=5):
    _load_resources()

    query_embedding = _model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    scores, indices = _index.search(query_embedding, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue

        doc = _docs[idx]
        results.append({
            "id": doc["id"],
            "text": doc["text"],
            "score": float(score)
        })

    return results

def retrieve_for_claim(claim: str, k: int = 5):
    """
    Retrieve evidence documents for a single normalized claim.
    """
    _load_resources()

    claim_embedding = _model.encode(
        [claim],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    scores, indices = _index.search(claim_embedding, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue

        doc = _docs[idx]
        results.append({
            "id": doc["id"],
            "text": doc["text"],
            "score": float(score)
        })

    return results
