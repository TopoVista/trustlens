"""FastAPI API routes for TrustLens"""
import time
import logging
from typing import List
from fastapi import APIRouter, HTTPException, status
from app.api.schemas import (
    QueryRequest,
    RAGResponse,
    AnalyzeResponse,
    HealthResponse,
    PipelineStats,
    VendorAssessmentRequest,
    VendorAssessmentResponse,
    QARequest,
    QAResponse,
    WorkspaceCreate,
    WorkspaceResponse,
    DocumentUploadRequest,
    DocumentResponse,
    SemanticRuleRequest,
    SemanticRuleResponse,
    KnowledgeHealthResponse,
    ProactiveDiscoveryResponse,
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
)
from app.pipeline.retriever import retrieve
from app.pipeline.generator import generate_answer
from app.pipeline.assembler import assemble_verified_answer
from app.pipeline.runner import run_rag
from app.evaluator.metrics import compute_summary_stats
from app.knowledge.repository import KnowledgeRepository
from app.specialists.ingestion_agent import IngestionKnowledgeAgent
from app.planner.planner import AnalysisPlanner

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


# --- Multi-Agent Extension Routes ---

@router.post("/api/assess", response_model=VendorAssessmentResponse)
async def assess_vendor(request: VendorAssessmentRequest):
    """
    Multi-Agent Vendor Security & Risk Assessment:
    Coordinates Ingestion, Parsing, Vector Retrieval, Compliance Mapping,
    Quantitative Risk Scoring, Findings Generation, and NLI Claim QA.
    """
    from app.agents.orchestrator import AgentOrchestrator
    orchestrator = AgentOrchestrator()

    try:
        result = await orchestrator.run_assessment(
            vendor_data=request.vendor.model_dump(),
            query=request.query,
            documents_text=request.documents_text
        )
        return result
    except Exception as e:
        logger.error("Multi-Agent assessment error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-Agent assessment failed: {str(e)}"
        )


@router.post("/api/ask", response_model=QAResponse)
async def ask_vendor_question(request: QARequest):
    """
    User Q&A Agent Endpoint:
    Answers analyst questions about vendor posture with verifiable citations.
    """
    from app.agents.qa_bot import UserQAAgent
    qa_agent = UserQAAgent()

    try:
        result = await qa_agent.answer_question(
            vendor_profile=request.vendor.model_dump(),
            question=request.question
        )
        return result
    except Exception as e:
        logger.error("User Q&A Agent error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Q&A inquiry failed: {str(e)}"
        )


# --- Personal Knowledge Intelligence Endpoints ---

_knowledge_repo = KnowledgeRepository()
_ingestion_agent = IngestionKnowledgeAgent(_knowledge_repo)
_planner = AnalysisPlanner(_knowledge_repo)


@router.get("/api/workspaces", response_model=List[WorkspaceResponse])
def list_workspaces():
    """Returns list of user workspaces, creating default if none exists."""
    _knowledge_repo.ensure_default_workspace()
    return _knowledge_repo.list_workspaces()


@router.post("/api/workspaces", response_model=WorkspaceResponse)
def create_workspace(request: WorkspaceCreate):
    """Creates a new isolated user knowledge workspace."""
    return _knowledge_repo.create_workspace(request.name, request.description)


@router.get("/api/workspaces/{workspace_id}/health", response_model=KnowledgeHealthResponse)
def get_workspace_health(workspace_id: str):
    """Calculates live knowledge health metrics for the workspace."""
    return _knowledge_repo.get_knowledge_health(workspace_id)


@router.get("/api/workspaces/{workspace_id}/discoveries", response_model=ProactiveDiscoveryResponse)
def get_workspace_discoveries(workspace_id: str):
    """Surfaces proactive 'Things You Should Know' discoveries."""
    discoveries = _knowledge_repo.get_proactive_discoveries(workspace_id)
    return {"discoveries": discoveries}


@router.post("/api/workspaces/{workspace_id}/documents", response_model=DocumentResponse)
async def upload_workspace_document(workspace_id: str, request: DocumentUploadRequest):
    """
    Ingests user documents/spreadsheets, extracting entities, claims, timeline events,
    and profiling structured CSV tables.
    """
    result = await _ingestion_agent.ingest_content(
        workspace_id=workspace_id,
        title=request.title,
        filename=request.filename or "document.txt",
        raw_content=request.raw_content,
        file_type=request.file_type or "text",
        authority_level=request.authority_level or "MEDIUM"
    )
    return result


@router.get("/api/workspaces/{workspace_id}/documents")
def get_workspace_documents(workspace_id: str):
    """Returns all ingested documents in the workspace."""
    return _knowledge_repo.get_documents(workspace_id)


@router.get("/api/workspaces/{workspace_id}/claims")
def get_workspace_claims(workspace_id: str):
    """Returns extracted claims with linked evidence."""
    return _knowledge_repo.get_claims(workspace_id)


@router.get("/api/workspaces/{workspace_id}/entities")
def get_workspace_entities(workspace_id: str):
    """Returns the Knowledge Graph nodes and edges for the workspace."""
    return _knowledge_repo.get_knowledge_graph(workspace_id)


@router.get("/api/workspaces/{workspace_id}/timeline")
def get_workspace_timeline(workspace_id: str):
    """Returns chronological timeline events."""
    return _knowledge_repo.get_timeline(workspace_id)


@router.get("/api/workspaces/{workspace_id}/rules", response_model=List[SemanticRuleResponse])
def get_workspace_rules(workspace_id: str):
    """Returns user-defined semantic memory rules."""
    return _knowledge_repo.get_semantic_rules(workspace_id)


@router.post("/api/workspaces/{workspace_id}/rules", response_model=SemanticRuleResponse)
def add_workspace_rule(workspace_id: str, request: SemanticRuleRequest):
    """Adds a user-defined semantic memory rule."""
    rule_id = _knowledge_repo.add_semantic_rule(
        workspace_id=workspace_id,
        rule_type=request.rule_type,
        rule_key=request.rule_key,
        rule_value=request.rule_value
    )
    rules = _knowledge_repo.get_semantic_rules(workspace_id)
    return next((r for r in rules if r["id"] == rule_id), None)


@router.post("/api/workspaces/{workspace_id}/query", response_model=KnowledgeQueryResponse)
async def query_workspace(workspace_id: str, request: KnowledgeQueryRequest):
    """
    Executes Intent-Aware Analysis Planner over user workspace knowledge.
    Returns response complying with Phase 11 Answer Contract.
    """
    try:
        response = await _planner.execute_plan(workspace_id, request.query)
        return response
    except Exception as e:
        logger.error("Workspace query error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge query failed: {str(e)}"
        )


