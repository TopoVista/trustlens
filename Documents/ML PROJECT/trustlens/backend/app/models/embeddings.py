"""Embeddings"""

import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

DOCS_PATH = "backend/data/processed_docs/docs.json"
INDEX_PATH = "backend/data/index.faiss"
STORE_PATH = "backend/data/doc_store.json"


def build_index():
    with open(DOCS_PATH, "r", encoding="utf-8") as f:
        documents = json.load(f)

    texts = [doc["text"] for doc in documents]

    model = SentenceTransformer("all-MiniLM-L6-v2")

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    dim = embeddings.shape[1]

    index = faiss.IndexFlatIP(dim)

    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)

    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)

    print(f"Indexed {len(documents)} documents")
    print(f"Embedding dimension: {dim}")

