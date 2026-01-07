"""routes"""
from fastapi import APIRouter
from app.api.schemas import QueryRequest, RAGResponse
from app.pipeline.runner import run_rag

""" imports for /analyze """
from app.pipeline.assembler import assemble_verified_answer
from app.pipeline.runner import run_rag
from app.api.schemas import AnalyzeResponse


router = APIRouter()


@router.post("/answer", response_model=RAGResponse)
def answer_query(request: QueryRequest):
    result = run_rag(query=request.query, k=request.k)

    return result

"""below is the code for the /analyze route """

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_query(request: QueryRequest):
    # 1. Run baseline RAG
    result = run_rag(query=request.query, k=request.k)
    answer = result["answer"]

    # 2. Verify answer at claim level
    verified_claims = assemble_verified_answer(answer, k=request.k)

    return {
        "query": request.query,
        "answer": answer,
        "verified_claims": verified_claims
    }
