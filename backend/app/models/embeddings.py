"""Embeddings and vector persistence utilities (OpenAI API backed, no torch/faiss).

Interfaces preserved for backward compatibility:

- ``get_embedding_model()`` -> object exposing ``encode(texts, ...)`` and
  ``get_model_name()`` so existing callers (``app.pipeline.retriever``,
  ``app.knowledge.hybrid_retriever``) require no changes.
- ``build_index()`` builds and persists corpus embeddings on disk
  (``corpus_embeddings.npy``) instead of a FAISS index.

Embedding strategy:
  * Query/document embeddings are generated with the OpenAI Embeddings API
    (``OPENAI_EMBEDDING_MODEL``, default ``text-embedding-3-small``).
  * Document embeddings are generated once and persisted (numpy file / SQLite
    blob tables), never regenerated per request.
  * Query embeddings are computed once per query and memoized in a bounded
    in-memory cache.
  * If the OpenAI API is unavailable (no key, network error, quota), a
    deterministic feature-hashing fallback keeps retrieval functional so the
    application never crashes.
"""
import hashlib
import json
import logging
import os
import re
import threading
from collections import OrderedDict
from pathlib import Path
from typing import List, Optional, Union

import numpy as np
from openai import OpenAI

logger = logging.getLogger("trustlens.embeddings")

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
DOCS_PATH = DATA_DIR / "processed_docs" / "docs.json"
INDEX_PATH = DATA_DIR / "index.faiss"  # legacy FAISS artifact, no longer needed at runtime
STORE_PATH = DATA_DIR / "doc_store.json"
CORPUS_EMBEDDINGS_PATH = DATA_DIR / "corpus_embeddings.npy"

DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"

# Dimensions used only for the deterministic offline fallback embedding.
_FALLBACK_DIM = 512
_MAX_QUERY_CACHE_ENTRIES = 1024

_singleton: Optional["EmbeddingService"] = None
_singleton_lock = threading.Lock()


def _hash_embedding(texts: List[str], dim: int = _FALLBACK_DIM) -> np.ndarray:
    """Deterministic feature-hashing embeddings (unigram+bigram) for offline use.

    Semantically weaker than OpenAI embeddings, but stable, dependency-free and
    sufficient to keep retrieval functional when no API key is configured.
    """
    rows = np.zeros((len(texts), dim), dtype=np.float32)
    for i, text in enumerate(texts):
        tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
        grams = list(tokens)
        for j in range(len(tokens) - 1):
            grams.append(tokens[j] + "_" + tokens[j + 1])
        for gram in grams:
            idx = int(hashlib.md5(gram.encode("utf-8")).hexdigest(), 16) % dim
            rows[i, idx] += 1.0
    norms = np.linalg.norm(rows, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return rows / norms


class EmbeddingService:
    """OpenAI-backed embedding service with a deterministic offline fallback."""

    def __init__(self, model: str):
        self.model = model or DEFAULT_OPENAI_EMBEDDING_MODEL
        self._client: Optional[OpenAI] = None
        self._lock = threading.Lock()
        self._query_cache: "OrderedDict[str, np.ndarray]" = OrderedDict()

    def get_model_name(self) -> str:
        return self.model

    def _get_client(self) -> OpenAI:
        api_key = os.getenv("OPENAI_API_KEY", "").strip().strip("\"'")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is missing.")
        if self._client is None:
            self._client = OpenAI(api_key=api_key)
        return self._client

    def _openai_embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a batch of texts via the OpenAI API."""
        client = self._get_client()
        vectors: List[np.ndarray] = []
        batch_size = 256
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            response = client.embeddings.create(model=self.model, input=batch)
            ordered = sorted(response.data, key=lambda d: getattr(d, "index", 0))
            vectors.extend([np.asarray(d.embedding, dtype=np.float32) for d in ordered])
        if not vectors:
            return np.zeros((0, 0), dtype=np.float32)
        return np.vstack(vectors).astype(np.float32)

    def encode(
        self,
        sentences: Union[str, List[str]],
        batch_size: int = 32,
        show_progress_bar: bool = False,
        convert_to_numpy: bool = True,
        normalize_embeddings: bool = False,
        **kwargs,
    ) -> Union[np.ndarray, List[List[float]]]:
        """Encode a string or list of strings into embeddings.

        Mirrors the previous SentenceTransformer.encode() surface used across
        the codebase:

            model.encode([query], convert_to_numpy=True, normalize_embeddings=True)

        Returns an ``np.ndarray`` of shape ``(n, d)`` when ``convert_to_numpy``
        is True (default), otherwise a list of vectors.
        """
        if isinstance(sentences, str):
            texts = [sentences]
            is_single = True
        else:
            texts = [s if isinstance(s, str) else str(s) for s in sentences]
            is_single = len(texts) == 1

        if not texts:
            return np.zeros((0, 0), dtype=np.float32) if convert_to_numpy else []

        if is_single:
            cached = self._query_cache.get(texts[0])
            if cached is not None:
                embeddings = cached
            else:
                embeddings = self._embed(texts)
                with self._lock:
                    self._query_cache[texts[0]] = embeddings
                    while len(self._query_cache) > _MAX_QUERY_CACHE_ENTRIES:
                        self._query_cache.popitem(last=False)
        else:
            embeddings = self._embed(texts)

        if normalize_embeddings:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            embeddings = embeddings / norms

        if convert_to_numpy:
            return embeddings
        return [v.tolist() for v in embeddings]

    def _embed(self, texts: List[str]) -> np.ndarray:
        """Produce embeddings, preferring OpenAI and falling back offline."""
        try:
            embeddings = self._openai_embed(texts)
            logger.debug("Embedded %d text(s) via OpenAI model '%s'", len(texts), self.model)
            return embeddings
        except Exception as e:  # noqa: BLE001 - must never crash the request
            logger.warning(
                "OpenAI embeddings unavailable (%s); using deterministic fallback "
                "embeddings for %d text(s).",
                e,
                len(texts),
            )
            return _hash_embedding(texts)


def get_embedding_model() -> EmbeddingService:
    """Return the shared embedding service singleton (lazy, thread-safe)."""
    global _singleton
    if _singleton is None:
        with _singleton_lock:
            if _singleton is None:
                model = os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_OPENAI_EMBEDDING_MODEL).strip()
                _singleton = EmbeddingService(model or DEFAULT_OPENAI_EMBEDDING_MODEL)
    return _singleton


def build_index():
    """Build and persist corpus embeddings from processed documents.

    Replaces the previous FAISS index builder. Writes ``corpus_embeddings.npy``
    and ``doc_store.json`` so retrieval never needs to re-embed the corpus.
    """
    if not DOCS_PATH.exists():
        raise FileNotFoundError(
            f"Processed documents not found at {DOCS_PATH}. Run corpus build script first."
        )

    with open(DOCS_PATH, "r", encoding="utf-8") as f:
        documents = json.load(f)

    texts = [doc["text"] for doc in documents]
    model = get_embedding_model()

    logger.info("Encoding %d documents with model '%s'...", len(texts), model.get_model_name())
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype(np.float32)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    np.save(CORPUS_EMBEDDINGS_PATH, embeddings)

    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)

    logger.info(
        "Built persisted corpus embeddings at %s with %d documents (dim=%d)",
        CORPUS_EMBEDDINGS_PATH,
        len(documents),
        embeddings.shape[1],
    )
    return len(documents)
