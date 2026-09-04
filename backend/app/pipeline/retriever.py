"""Retriever module: semantic FAISS retrieval with all-MiniLM-L6-v2"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
import faiss
import numpy as np
from app.models.embeddings import get_embedding_model

logger = logging.getLogger("trustlens.retriever")

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
INDEX_PATH = DATA_DIR / "index.faiss"
DOC_STORE_PATH = DATA_DIR / "doc_store.json"

DEFAULT_RETRIEVAL_K = int(os.getenv("RETRIEVAL_K", "5"))
DEFAULT_CLAIM_RETRIEVAL_K = int(os.getenv("CLAIM_RETRIEVAL_K", "3"))

_index = None
_docs = None


def _load_resources():
    global _index, _docs

    if _index is None:
        if not INDEX_PATH.exists():
            logger.error("FAISS index not found at %s", INDEX_PATH)
            raise FileNotFoundError(
                f"FAISS index file missing at {INDEX_PATH}. "
                "Ensure backend corpus generation has been executed."
            )
        logger.info("Reading FAISS index from %s", INDEX_PATH)
        _index = faiss.read_index(str(INDEX_PATH))

    if _docs is None:
        if not DOC_STORE_PATH.exists():
            logger.error("Document store not found at %s", DOC_STORE_PATH)
            raise FileNotFoundError(
                f"Document store missing at {DOC_STORE_PATH}. "
                "Ensure backend corpus generation has been executed."
            )
        logger.info("Reading document store from %s", DOC_STORE_PATH)
        with open(DOC_STORE_PATH, "r", encoding="utf-8") as f:
            _docs = json.load(f)


def retrieve(query: str, k: Optional[int] = None) -> List[Dict]:
    """
    Retrieve top-k relevant documents for a general query.
    """
    if not query or not query.strip():
        return []

    _load_resources()
    limit = k if k is not None else DEFAULT_RETRIEVAL_K
    limit = max(1, min(limit, 10))  # Sanity bounds

    model = get_embedding_model()
    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    ).astype("float32")

    scores, indices = _index.search(query_embedding, min(limit, len(_docs)))

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(_docs):
            continue
        doc = _docs[idx]
        results.append({
            "id": doc.get("id", f"doc_{idx:03d}"),
            "text": doc.get("text", ""),
            "score": round(float(score), 4)
        })

    return results


def retrieve_for_claim(claim: str, k: Optional[int] = None) -> List[Dict]:
    """
    Retrieve evidence documents specifically matching an extracted claim.
    """
    if not claim or not claim.strip():
        return []

    _load_resources()
    limit = k if k is not None else DEFAULT_CLAIM_RETRIEVAL_K
    limit = max(1, min(limit, 10))

    model = get_embedding_model()
    claim_embedding = model.encode(
        [claim],
        convert_to_numpy=True,
        normalize_embeddings=True
    ).astype("float32")

    scores, indices = _index.search(claim_embedding, min(limit, len(_docs)))

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(_docs):
            continue
        doc = _docs[idx]
        results.append({
            "id": doc.get("id", f"doc_{idx:03d}"),
            "text": doc.get("text", ""),
            "score": round(float(score), 4)
        })

    return results
