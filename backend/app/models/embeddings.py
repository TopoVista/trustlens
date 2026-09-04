"""Embeddings and FAISS indexing utilities"""
import os
import json
import logging
from pathlib import Path
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("trustlens.embeddings")

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
DOCS_PATH = DATA_DIR / "processed_docs" / "docs.json"
INDEX_PATH = DATA_DIR / "index.faiss"
STORE_PATH = DATA_DIR / "doc_store.json"

_embedding_model = None


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading SentenceTransformer ('all-MiniLM-L6-v2')...")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


def build_index():
    """
    Build FAISS IndexFlatIP from processed documents and save index + doc store.
    """
    if not DOCS_PATH.exists():
        raise FileNotFoundError(f"Processed documents not found at {DOCS_PATH}. Run corpus build script first.")

    with open(DOCS_PATH, "r", encoding="utf-8") as f:
        documents = json.load(f)

    texts = [doc["text"] for doc in documents]
    model = get_embedding_model()

    logger.info("Encoding %d documents...", len(texts))
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings.astype("float32"))

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))

    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)

    logger.info("Successfully built FAISS index at %s with %d documents (dim=%d)", INDEX_PATH, len(documents), dim)
    return len(documents)
