"""Retriever module: semantic retrieval with persisted vectors + NumPy (no FAISS).

Public interface preserved:

- ``retrieve(query, k=None)``
- ``retrieve_for_claim(claim, k=None)``
- ``_load_resources()``

Both functions return a list of ``{"id", "text", "score"}`` dicts exactly as
before. The corpus embeddings are loaded from ``corpus_embeddings.npy`` and
built + persisted on first use if missing.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from app.models.embeddings import CORPUS_EMBEDDINGS_PATH, get_embedding_model

logger = logging.getLogger("trustlens.retriever")

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
INDEX_PATH = DATA_DIR / "index.faiss"  # legacy FAISS artifact, no longer used at runtime
DOC_STORE_PATH = DATA_DIR / "doc_store.json"

DEFAULT_RETRIEVAL_K = int(os.getenv("RETRIEVAL_K", "5"))
DEFAULT_CLAIM_RETRIEVAL_K = int(os.getenv("CLAIM_RETRIEVAL_K", "3"))

_index: Optional[np.ndarray] = None
_docs: Optional[List[Dict]] = None


def _load_resources():
    """Load the document store and the persisted corpus embeddings matrix."""
    global _index, _docs

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

    if _index is None:
        if CORPUS_EMBEDDINGS_PATH.exists():
            logger.info("Reading persisted corpus embeddings from %s", CORPUS_EMBEDDINGS_PATH)
            _index = np.load(CORPUS_EMBEDDINGS_PATH).astype(np.float32)
        else:
            model = get_embedding_model()
            texts = [doc.get("text", "") for doc in _docs]
            logger.info(
                "Building persisted corpus embeddings once for %d documents via '%s'...",
                len(texts),
                model.get_model_name(),
            )
            CORPUS_EMBEDDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            _index = model.encode(
                texts, convert_to_numpy=True, normalize_embeddings=True
            ).astype(np.float32)
            np.save(CORPUS_EMBEDDINGS_PATH, _index)
            logger.info("Persisted corpus embeddings to %s (dim=%d)", CORPUS_EMBEDDINGS_PATH, _index.shape[1])

    if len(_index) != len(_docs):
        logger.warning(
            "Corpus embedding count (%d) does not match document count (%d). "
            "Rebuild with scripts/build_corpus_embeddings.py.",
            len(_index),
            len(_docs),
        )

    return _index, _docs


def _rebuild_index() -> np.ndarray:
    """Re-embed and persist the whole corpus once (self-healing on dim drift)."""
    global _index
    model = get_embedding_model()
    texts = [doc.get("text", "") for doc in (_docs or [])]
    logger.info(
        "Rebuilding persisted corpus embeddings for %d documents via '%s'...",
        len(texts),
        model.get_model_name(),
    )
    CORPUS_EMBEDDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    matrix = model.encode(
        texts, convert_to_numpy=True, normalize_embeddings=True
    ).astype(np.float32)
    np.save(CORPUS_EMBEDDINGS_PATH, matrix)
    _index = matrix
    logger.info(
        "Persisted rebuilt corpus embeddings to %s (dim=%d)",
        CORPUS_EMBEDDINGS_PATH,
        matrix.shape[1],
    )
    return matrix


_rebuild_lock_held = False


def _search(query: str, k: int) -> List[Dict]:
    """Vector similarity search over the persisted corpus embeddings."""
    index, docs = _load_resources()
    model = get_embedding_model()
    query_embedding = model.encode(
        [query], convert_to_numpy=True, normalize_embeddings=True
    ).astype(np.float32).reshape(-1)

    if index.ndim == 2 and index.shape[1] != query_embedding.shape[0]:
        # Dimension drift: the persisted matrix was produced by a different
        # embedding model (e.g. offline fallback during an API outage, or an
        # older configured model). Re-embed + persist once so search stays
        # valid instead of crashing the request.
        global _rebuild_lock_held
        if _rebuild_lock_held:
            logger.error(
                "Corpus dimension drift persists after rebuild; skipping search."
            )
            return []
        _rebuild_lock_held = True
        try:
            index = _rebuild_index()
        finally:
            _rebuild_lock_held = False

    scores = np.dot(index, query_embedding)
    top_positions = np.argsort(scores)[::-1][:k]

    results: List[Dict] = []
    for pos in top_positions:
        if pos < 0 or pos >= len(docs):
            continue
        doc = docs[pos]
        results.append({
            "id": doc.get("id", f"doc_{int(pos) + 1:03d}"),
            "text": doc.get("text", ""),
            "score": round(float(scores[pos]), 4),
        })
    return results


def retrieve(query: str, k: Optional[int] = None) -> List[Dict]:
    """
    Retrieve top-k relevant documents for a general query.
    """
    if not query or not query.strip():
        return []

    limit = k if k is not None else DEFAULT_RETRIEVAL_K
    limit = max(1, min(limit, 10))  # Sanity bounds

    return _search(query, limit)


def retrieve_for_claim(claim: str, k: Optional[int] = None) -> List[Dict]:
    """
    Retrieve evidence documents specifically matching an extracted claim.
    """
    if not claim or not claim.strip():
        return []

    limit = k if k is not None else DEFAULT_CLAIM_RETRIEVAL_K
    limit = max(1, min(limit, 10))

    return _search(claim, limit)
