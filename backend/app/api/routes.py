"""FastAPI API routes for TrustLens"""
import time
import logging
from fastapi import APIRouter, HTTPException, status
from app.api.schemas import (
    QueryRequest,
    RAGResponse,
    AnalyzeResponse,
    HealthResponse,
    PipelineStats
)
from app.pipeline.retriever import retrieve
from app.pipeline.generator import generate_answer
from app.pipeline.assembler import assemble_verified_answer
from app.pipeline.runner import run_rag
from app.evaluator.metrics import compute_summary_stats

logger = logging.getLogger("trustlens.routes")
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    """
    Lightweight health endpoint for Render and uptime monitoring.
    Never loads ML models or calls external APIs.
    """
    return {
        "status": "ok",
        "version": "2.0.0"
    }


@router.post("/answer", response_model=RAGResponse)
def answer_query(request: QueryRequest):
    """
    Baseline RAG endpoint:
    Retrieves documents and generates an answer without claim verification.
    """
    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query must not be empty."
        )

    try:
        result = run_rag(query=query_text, k=request.k)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        logger.error("Generation error in /answer: %s", e)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except FileNotFoundError as e:
        logger.error("Index not found in /answer: %s", e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.error("Unhandled exception in /answer: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_query(request: QueryRequest):
    """
    Full TrustLens Verification Pipeline:
    1. Independent semantic retrieval
    2. Grounded OpenAI generation
    3. Sentence-level claim decomposition
    4. Independent claim-level retrieval & NLI verification
    5. Latency profiling & summary evaluation metrics
    """
    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query must not be empty."
        )

    total_start = time.perf_counter()

    # Step 1: Retrieval for generation
    t0 = time.perf_counter()
    try:
        documents = retrieve(query_text, k=request.k)
    except FileNotFoundError as e:
        logger.error("FAISS index error: %s", e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    retrieval_ms = round((time.perf_counter() - t0) * 1000, 1)

    # Step 2: Grounded generation
    t1 = time.perf_counter()
    try:
        answer = generate_answer(query_text, documents)
    except (RuntimeError, ValueError) as e:
        logger.error("Generation error: %s", e)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        logger.error("Unhandled generation error: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Generation error: {str(e)}")
    generation_ms = round((time.perf_counter() - t1) * 1000, 1)

    # Step 3 & 4: Claim extraction, claim-level retrieval, and NLI verification
    t2 = time.perf_counter()
    try:
        verified_claims = assemble_verified_answer(answer)
    except Exception as e:
        logger.error("Verification error: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Verification error: {str(e)}")
    verification_ms = round((time.perf_counter() - t2) * 1000, 1)

    total_ms = round((time.perf_counter() - total_start) * 1000, 1)

    # Step 5: Metric calculation
    summary = compute_summary_stats(verified_claims)
    stats = PipelineStats(
        claim_count=summary["claim_count"],
        supported=summary["supported"],
        not_supported=summary["not_supported"],
        contradicted=summary["contradicted"],
        faithfulness=summary["faithfulness"],
        hallucination_rate=summary["hallucination_rate"],
        retrieval_ms=retrieval_ms,
        generation_ms=generation_ms,
        verification_ms=verification_ms,
        total_ms=total_ms
    )

    return {
        "query": query_text,
        "answer": answer,
        "documents": documents,
        "verified_claims": verified_claims,
        "stats": stats
    }
