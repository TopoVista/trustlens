"""FastAPI API routes for TrustLens"""
import sys
import time
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, status, Depends
from app.api.auth import AuthUser, get_current_user, get_current_user_context
from app.knowledge.user_storage import UserKnowledgeContext, get_user_storage_stats
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


@router.get("/health/ready")
def readiness_check():
    """
    Readiness probe: verifies the process can serve requests and that the
    knowledge database is reachable. Performs no model loading and no
    external API calls, so it is safe to poll frequently.
    """
    db_ok = False
    try:
        from app.knowledge.db import ensure_schema, DEFAULT_DB_PATH
        ensure_schema()
        db_ok = DEFAULT_DB_PATH.exists()
    except Exception:  # noqa: BLE001 - readiness must never raise
        logger.exception("Readiness check: knowledge database unavailable.")
    return {
        "status": "ready" if db_ok else "degraded",
        "version": "2.0.0",
        "database": db_ok,
    }


def _read_rss_mb() -> Optional[float]:
    """Best-effort RSS measurement without required external dependencies."""
    try:  # optional accelerator (dev machines); never required in production
        import psutil  # type: ignore
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except ImportError:
        pass
    try:
        # Linux (Render): parse /proc/self/status
        with open("/proc/self/status", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / 1024.0  # kB -> MB
    except OSError:
        pass
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class _PMC(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t),
                            ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t),
                            ("PeakPagefileUsage", ctypes.c_size_t)]

            pmc = _PMC()
            pmc.cb = ctypes.sizeof(_PMC)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(pmc), pmc.cb):
                return pmc.WorkingSetSize / (1024 * 1024)
        except Exception:  # noqa: BLE001
            return None
    return None


def _read_cgroup_limit_mb() -> Optional[float]:
    """Read the container memory limit from cgroup v2/v1 (Render enforces it)."""
    for path in ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                raw = fh.read().strip()
            if raw and raw != "max":
                return float(raw) / (1024 * 1024)
        except OSError:
            continue
    return None


@router.get("/health/memory")
def memory_health():
    """
    Memory diagnostics for Render Free capacity monitoring.
    Reports process RSS and the container cgroup limit (when running under
    Linux containers). Exposes no sensitive configuration.
    """
    rss = _read_rss_mb()
    limit = _read_cgroup_limit_mb()
    body = {
        "status": "ok",
        "rss_mb": round(rss, 1) if rss is not None else None,
    }
    if limit is not None:
        body["limit_mb"] = round(limit, 1)
        body["usage_percent"] = round((rss / limit) * 100, 1) if rss is not None else None
        body["status"] = "ok" if (rss is None or rss < limit * 0.85) else "warning"
    return body


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


# --- Personal Knowledge Intelligence Endpoints (Strict Per-User Hard Disk Isolation) ---

@router.get("/api/me")
def get_me(user: AuthUser = Depends(get_current_user)):
    """Returns the authenticated user details."""
    return {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "is_authenticated": user.is_authenticated
    }


@router.get("/api/me/storage")
def get_my_storage(user: AuthUser = Depends(get_current_user)):
    """Returns local hard disk partition path and usage metrics for this user."""
    return get_user_storage_stats(user.user_id)


@router.get("/api/workspaces", response_model=List[WorkspaceResponse])
def list_workspaces(ctx: UserKnowledgeContext = Depends(get_current_user_context)):
    """Returns list of user workspaces, creating default if none exists."""
    ctx.repo.ensure_default_workspace()
    return ctx.repo.list_workspaces()


@router.post("/api/workspaces", response_model=WorkspaceResponse)
def create_workspace(
    request: WorkspaceCreate,
    ctx: UserKnowledgeContext = Depends(get_current_user_context)
):
    """Creates a new isolated user knowledge workspace."""
    return ctx.repo.create_workspace(request.name, request.description)


@router.get("/api/workspaces/{workspace_id}/health", response_model=KnowledgeHealthResponse)
def get_workspace_health(
    workspace_id: str,
    ctx: UserKnowledgeContext = Depends(get_current_user_context)
):
    """Calculates live knowledge health metrics for the workspace."""
    return ctx.repo.get_knowledge_health(workspace_id)


@router.get("/api/workspaces/{workspace_id}/discoveries", response_model=ProactiveDiscoveryResponse)
def get_workspace_discoveries(
    workspace_id: str,
    ctx: UserKnowledgeContext = Depends(get_current_user_context)
):
    """Surfaces proactive 'Things You Should Know' discoveries."""
    discoveries = ctx.repo.get_proactive_discoveries(workspace_id)
    return {"discoveries": discoveries}


@router.post("/api/workspaces/{workspace_id}/documents", response_model=DocumentResponse)
async def upload_workspace_document(
    workspace_id: str,
    request: DocumentUploadRequest,
    ctx: UserKnowledgeContext = Depends(get_current_user_context)
):
    """
    Ingests user documents/spreadsheets, extracting entities, claims, timeline events,
    and profiling structured CSV tables into the user's isolated hard drive storage.
    """
    result = await ctx.ingestion_agent.ingest_content(
        workspace_id=workspace_id,
        title=request.title,
        filename=request.filename or "document.txt",
        raw_content=request.raw_content,
        file_type=request.file_type or "text",
        authority_level=request.authority_level or "MEDIUM"
    )
    return result


@router.get("/api/workspaces/{workspace_id}/documents")
def get_workspace_documents(
    workspace_id: str,
    ctx: UserKnowledgeContext = Depends(get_current_user_context)
):
    """Returns all ingested documents in the workspace."""
    return ctx.repo.get_documents(workspace_id)


@router.get("/api/workspaces/{workspace_id}/claims")
def get_workspace_claims(
    workspace_id: str,
    ctx: UserKnowledgeContext = Depends(get_current_user_context)
):
    """Returns extracted claims with linked evidence."""
    return ctx.repo.get_claims(workspace_id)


@router.get("/api/workspaces/{workspace_id}/entities")
def get_workspace_entities(
    workspace_id: str,
    ctx: UserKnowledgeContext = Depends(get_current_user_context)
):
    """Returns the Knowledge Graph nodes and edges for the workspace."""
    return ctx.repo.get_knowledge_graph(workspace_id)


@router.get("/api/workspaces/{workspace_id}/timeline")
def get_workspace_timeline(
    workspace_id: str,
    ctx: UserKnowledgeContext = Depends(get_current_user_context)
):
    """Returns chronological timeline events."""
    return ctx.repo.get_timeline(workspace_id)


@router.get("/api/workspaces/{workspace_id}/rules", response_model=List[SemanticRuleResponse])
def get_workspace_rules(
    workspace_id: str,
    ctx: UserKnowledgeContext = Depends(get_current_user_context)
):
    """Returns user-defined semantic memory rules."""
    return ctx.repo.get_semantic_rules(workspace_id)


@router.post("/api/workspaces/{workspace_id}/rules", response_model=SemanticRuleResponse)
def add_workspace_rule(
    workspace_id: str,
    request: SemanticRuleRequest,
    ctx: UserKnowledgeContext = Depends(get_current_user_context)
):
    """Adds a user-defined semantic memory rule."""
    rule_id = ctx.repo.add_semantic_rule(
        workspace_id=workspace_id,
        rule_type=request.rule_type,
        rule_key=request.rule_key,
        rule_value=request.rule_value
    )
    rules = ctx.repo.get_semantic_rules(workspace_id)
    return next((r for r in rules if r["id"] == rule_id), None)


@router.post("/api/workspaces/{workspace_id}/query", response_model=KnowledgeQueryResponse)
async def query_workspace(
    workspace_id: str,
    request: KnowledgeQueryRequest,
    ctx: UserKnowledgeContext = Depends(get_current_user_context)
):
    """
    Executes Intent-Aware Analysis Planner over user workspace knowledge.
    Returns response complying with Phase 11 Answer Contract.
    """
    try:
        response = await ctx.planner.execute_plan(workspace_id, request.query)
        return response
    except Exception as e:
        logger.error("Workspace query error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge query failed: {str(e)}"
        )



# --- Dataset Analytics endpoints ----------------------------------------

from app.data.storage import store_upload, get_metadata, get_path, list_datasets
from app.data.session import get_session
from app.analytics.profiling import profile_dataset, read_dataset
from app.analytics.eda import compute_statistics, compute_correlations, detect_outliers_iqr
from app.analytics.insights import detect_insights
from app.analytics.charts import suggest_charts


def _require_user(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    return user


@router.post("/datasets/upload")
async def upload_dataset(
    request: Request,
    user: AuthUser = Depends(_require_user),
):
    """Upload a dataset file (CSV/JSON/Parquet/Excel) for analysis.

    Accepts either:
      - a raw request body (e.g. ``curl --data-binary @file.csv
        ".../datasets/upload?filename=file.csv&source_type=csv"``), or
      - a standard multipart/form-data upload with a ``file`` field
        (only when the optional ``python-multipart`` package is installed).
    """
    content: Optional[bytes] = None
    filename = "dataset.csv"
    source_type = "csv"
    content_type = request.headers.get("content-type", "")

    if content_type.startswith("multipart/form-data"):
        try:
            form = await request.form()
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Multipart upload requires the optional 'python-multipart' "
                       "dependency. Send a raw request body with ?filename= instead.",
            )
        upload = form.get("file")
        if upload is None or isinstance(upload, str):
            raise HTTPException(status_code=400, detail="Multipart field 'file' is required.")
        content = await upload.read()
        filename = form.get("filename") or upload.filename or filename
        source_type = form.get("source_type") or "csv"
    else:
        content = await request.body()
        filename = request.query_params.get("filename", filename)
        source_type = request.query_params.get("source_type", "csv")

    if not content:
        raise HTTPException(status_code=400, detail="No file content provided.")
    try:
        dataset_id = store_upload(str(filename), content, str(source_type))
        session = get_session(dataset_id)
        return {"dataset_id": dataset_id, "filename": session.filename, "status": "uploaded", "session": session.to_dict()}
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {e}")


@router.post("/datasets/profile")
def profile_uploaded_dataset(
    dataset_id: str,
    user: AuthUser = Depends(_require_user),
):
    """Profile an uploaded dataset and return structured metadata."""
    session = get_session(dataset_id)
    if not session.exists:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    path = session.file_path
    if not path:
        raise HTTPException(status_code=404, detail="Dataset file missing on disk.")
    try:
        profile = profile_dataset(session.filename, str(path), dataset_id)
        return profile.to_dict()
    except ImportError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Profiling error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Profiling failed: {e}")


@router.get("/datasets")
def list_all_datasets(user: AuthUser = Depends(_require_user)):
    """List all uploaded datasets."""
    datasets = list_datasets()
    return {"datasets": [{"id": k, **v} for k, v in datasets.items()]}


@router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: str, user: AuthUser = Depends(_require_user)):
    """Return dataset session metadata."""
    session = get_session(dataset_id)
    if not session.exists:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    return session.to_dict()


@router.post("/datasets/{dataset_id}/eda")
def run_eda(dataset_id: str, user: AuthUser = Depends(_require_user)):
    """Run deterministic EDA on a dataset and return structured statistics."""
    session = get_session(dataset_id)
    if not session.exists:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    path = session.file_path
    if not path:
        raise HTTPException(status_code=404, detail="Dataset file missing on disk.")
    try:
        headers, rows = read_dataset(session.filename, str(path))
        numeric_cols = []
        stats = {}
        correlations = []
        outliers = {}

        # Compute stats for numeric columns
        col_values = {}
        for i, name in enumerate(headers):
            col_values[name] = [row[i] if i < len(row) else None for row in rows]
            nums = [v for v in col_values[name] if v is not None and str(v).strip() != ""]
            try:
                [float(str(v).replace(",", "")) for v in nums[:10]]
                numeric_cols.append(name)
            except (ValueError, TypeError):
                pass

        for name in numeric_cols:
            stats[name] = compute_statistics(col_values[name])

        if len(numeric_cols) >= 2:
            correlations = compute_correlations(headers, rows, numeric_cols)

        for name in numeric_cols:
            outliers[name] = detect_outliers_iqr(col_values[name])

        return {
            "dataset_id": dataset_id,
            "row_count": len(rows),
            "column_count": len(headers),
            "numeric_columns": numeric_cols,
            "statistics": stats,
            "correlations": correlations,
            "outliers": outliers,
        }
    except ImportError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("EDA error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"EDA failed: {e}")


@router.get("/datasets/{dataset_id}/insights")
def get_insights(dataset_id: str, user: AuthUser = Depends(_require_user)):
    """Generate deterministic insights from a dataset."""
    session = get_session(dataset_id)
    if not session.exists:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    path = session.file_path
    if not path:
        raise HTTPException(status_code=404, detail="Dataset file missing on disk.")
    try:
        profile = profile_dataset(session.filename, str(path), dataset_id)
        headers, rows = read_dataset(session.filename, str(path))
        insights_list = detect_insights(profile, headers, rows)
        return {
            "dataset_id": dataset_id,
            "insights": [i.to_dict() for i in insights_list],
            "profile": profile.to_dict(),
        }
    except ImportError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Insights error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Insights failed: {e}")


@router.get("/datasets/{dataset_id}/charts")
def get_charts(dataset_id: str, user: AuthUser = Depends(_require_user)):
    """Generate chart specifications for a dataset."""
    session = get_session(dataset_id)
    if not session.exists:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    path = session.file_path
    if not path:
        raise HTTPException(status_code=404, detail="Dataset file missing on disk.")
    try:
        profile = profile_dataset(session.filename, str(path), dataset_id)
        charts = suggest_charts(profile)
        return {
            "dataset_id": dataset_id,
            "charts": [c.to_dict() for c in charts],
        }
    except ImportError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Charts error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Charts failed: {e}")


@router.delete("/datasets/{dataset_id}")
def delete_dataset_endpoint(dataset_id: str, user: AuthUser = Depends(_require_user)):
    """Delete an uploaded dataset and its stored file."""
    from app.data.storage import delete_dataset
    from app.data.session import evict_session

    if not delete_dataset(dataset_id):
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    evict_session(dataset_id)
    return {"dataset_id": dataset_id, "status": "deleted"}


