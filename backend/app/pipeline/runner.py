"""Pipeline runner for baseline RAG execution"""
import logging
from app.pipeline.retriever import retrieve
from app.pipeline.generator import generate_answer

logger = logging.getLogger("trustlens.runner")


def run_rag(query: str, k: int = 5) -> dict:
    """
    Execute baseline RAG pipeline:
    1. Retrieve top-k evidence documents
    2. Generate grounded answer with OpenAI
    """
    clean_query = query.strip()
    if not clean_query:
        raise ValueError("Query must not be empty.")

    logger.info("Executing baseline RAG for query: '%s...' (k=%d)", clean_query[:50], k)

    docs = retrieve(clean_query, k=k)
    answer = generate_answer(clean_query, docs)

    return {
        "query": clean_query,
        "answer": answer,
        "documents": docs
    }
