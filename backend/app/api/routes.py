"""FastAPI API routes for TrustLens"""
import asyncio
import json
import sys
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from app.api.auth import AuthUser, enforce_workspace_ownership, get_current_user, get_current_user_context
from app.knowledge.user_storage import UserKnowledgeContext, get_user_storage_stats
from app.api.schemas import (
    HealthResponse,
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
    WorkspaceGraphResponse,
)
from app.planner.planner import AnalysisPlanner
from app.knowledge.graph_builder import GraphBuilder
from app.knowledge.graph_queries import GraphQueries
from app.specialists.relationship_agent import RelationshipAgent

logger = logging.getLogger("trustlens.routes")
router = APIRouter()


def _sse_event(event: str, payload: dict) -> str:
    """Encode a single Server-Sent Event without allowing line injection."""
    return f"event: {event}\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n"


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


# --- Personal Knowledge Intelligence Endpoints (Strict Per-User Hard Disk Isolation) ---


@router.get("/api/me/storage")
def get_my_storage(user: AuthUser = Depends(get_current_user)):
    """Returns local hard disk partition path and usage metrics for this user."""
    return get_user_storage_stats(user.user_id)


@router.get("/api/workspaces", response_model=List[WorkspaceResponse])
def list_workspaces(
    user: AuthUser = Depends(get_current_user),
    ctx: UserKnowledgeContext = Depends(get_current_user_context),
):
    """Returns list of user workspaces, creating default if none exists."""
    ctx.repo.ensure_default_workspace(owner_user_id=user.user_id)
    return ctx.repo.list_workspaces(owner_user_id=user.user_id)


@router.post("/api/workspaces", response_model=WorkspaceResponse)
def create_workspace(
    request: WorkspaceCreate,
    user: AuthUser = Depends(get_current_user),
    ctx: UserKnowledgeContext = Depends(get_current_user_context),
):
    """Creates a new isolated user knowledge workspace."""
    return ctx.repo.create_workspace(
        request.name, request.description, owner_user_id=user.user_id
    )


@router.get("/api/workspaces/{workspace_id}/health", response_model=KnowledgeHealthResponse)
def get_workspace_health(
    workspace_id: str,
    user: AuthUser = Depends(get_current_user),
    ctx: UserKnowledgeContext = Depends(get_current_user_context),
):
    """Calculates live knowledge health metrics for the workspace."""
    enforce_workspace_ownership(user, workspace_id, ctx.repo)
    return ctx.repo.get_knowledge_health(workspace_id)


@router.get("/api/workspaces/{workspace_id}/discoveries", response_model=ProactiveDiscoveryResponse)
def get_workspace_discoveries(
    workspace_id: str,
    user: AuthUser = Depends(get_current_user),
    ctx: UserKnowledgeContext = Depends(get_current_user_context),
):
    """Surfaces proactive 'Things You Should Know' discoveries."""
    enforce_workspace_ownership(user, workspace_id, ctx.repo)
    discoveries = ctx.repo.get_proactive_discoveries(workspace_id)
    return {"discoveries": discoveries}


@router.post("/api/workspaces/{workspace_id}/documents", response_model=DocumentResponse)
async def upload_workspace_document(
    workspace_id: str,
    request: DocumentUploadRequest,
    user: AuthUser = Depends(get_current_user),
    ctx: UserKnowledgeContext = Depends(get_current_user_context),
):
    """
    Ingests user documents/spreadsheets, extracting entities, claims, timeline events,
    and profiling structured CSV tables into the user's isolated hard drive storage.
    """
    enforce_workspace_ownership(user, workspace_id, ctx.repo)
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
    user: AuthUser = Depends(get_current_user),
    ctx: UserKnowledgeContext = Depends(get_current_user_context),
):
    """Returns all ingested documents in the workspace."""
    enforce_workspace_ownership(user, workspace_id, ctx.repo)
    return ctx.repo.get_documents(workspace_id)


@router.get("/api/workspaces/{workspace_id}/claims")
def get_workspace_claims(
    workspace_id: str,
    user: AuthUser = Depends(get_current_user),
    ctx: UserKnowledgeContext = Depends(get_current_user_context),
):
    """Returns extracted claims with linked evidence."""
    enforce_workspace_ownership(user, workspace_id, ctx.repo)
    return ctx.repo.get_claims(workspace_id)


@router.get("/api/workspaces/{workspace_id}/entities")
def get_workspace_entities(
    workspace_id: str,
    user: AuthUser = Depends(get_current_user),
    ctx: UserKnowledgeContext = Depends(get_current_user_context),
):
    """Returns the Knowledge Graph nodes and edges for the workspace."""
    enforce_workspace_ownership(user, workspace_id, ctx.repo)
    return ctx.repo.get_knowledge_graph(workspace_id)


@router.get("/api/workspaces/{workspace_id}/graph", response_model=WorkspaceGraphResponse)
def get_workspace_graph(
    workspace_id: str,
    mode: str = Query("all", pattern="^(all|claims|entities|variables|evidence|contradictions|dependencies|data)$"),
    min_confidence: float = Query(0.5, ge=0.0, le=1.0),
    document_id: Optional[str] = None,
    limit: int = Query(1000, ge=1, le=2000),
    user: AuthUser = Depends(get_current_user),
    ctx: UserKnowledgeContext = Depends(get_current_user_context),
):
    """Return the evidence-backed graph projection for one authorized workspace."""
    enforce_workspace_ownership(user, workspace_id, ctx.repo)
    # Existing documents predating graph projection are upgraded lazily without
    # requiring destructive migration or a separate maintenance service.
    if ctx.repo.get_graph_stats(workspace_id)["nodes"] == 0 and ctx.repo.get_documents(workspace_id):
        for document in ctx.repo.get_documents(workspace_id):
            RelationshipAgent(ctx.repo).enrich_document(workspace_id, document["id"])
        GraphBuilder(ctx.repo).rebuild_workspace(workspace_id)
    return GraphQueries(ctx.repo).graph(workspace_id, mode, min_confidence, document_id, limit)


@router.get("/api/workspaces/{workspace_id}/graph/nodes/{node_id}")
def get_workspace_graph_node(
    workspace_id: str,
    node_id: str,
    user: AuthUser = Depends(get_current_user),
    ctx: UserKnowledgeContext = Depends(get_current_user_context),
):
    enforce_workspace_ownership(user, workspace_id, ctx.repo)
    result = GraphQueries(ctx.repo).node_detail(workspace_id, node_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph node not found.")
    return result


@router.get("/api/workspaces/{workspace_id}/graph/path")
def get_workspace_graph_path(
    workspace_id: str,
    source: str = Query(..., min_length=1),
    target: str = Query(..., min_length=1),
    user: AuthUser = Depends(get_current_user),
    ctx: UserKnowledgeContext = Depends(get_current_user_context),
):
    enforce_workspace_ownership(user, workspace_id, ctx.repo)
    result = GraphQueries(ctx.repo).path(workspace_id, source, target)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph node not found.")
    return result


@router.get("/api/workspaces/{workspace_id}/timeline")
def get_workspace_timeline(
    workspace_id: str,
    user: AuthUser = Depends(get_current_user),
    ctx: UserKnowledgeContext = Depends(get_current_user_context),
):
    """Returns chronological timeline events."""
    enforce_workspace_ownership(user, workspace_id, ctx.repo)
    return ctx.repo.get_timeline(workspace_id)


@router.get("/api/workspaces/{workspace_id}/rules", response_model=List[SemanticRuleResponse])
def get_workspace_rules(
    workspace_id: str,
    user: AuthUser = Depends(get_current_user),
    ctx: UserKnowledgeContext = Depends(get_current_user_context),
):
    """Returns user-defined semantic memory rules."""
    enforce_workspace_ownership(user, workspace_id, ctx.repo)
    return ctx.repo.get_semantic_rules(workspace_id)


@router.post("/api/workspaces/{workspace_id}/rules", response_model=SemanticRuleResponse)
def add_workspace_rule(
    workspace_id: str,
    request: SemanticRuleRequest,
    user: AuthUser = Depends(get_current_user),
    ctx: UserKnowledgeContext = Depends(get_current_user_context),
):
    """Adds a user-defined semantic memory rule."""
    enforce_workspace_ownership(user, workspace_id, ctx.repo)
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
    user: AuthUser = Depends(get_current_user),
    ctx: UserKnowledgeContext = Depends(get_current_user_context),
):
    """
    Executes Intent-Aware Analysis Planner over user workspace knowledge.
    Returns response complying with Phase 11 Answer Contract.
    """
    enforce_workspace_ownership(user, workspace_id, ctx.repo)
    try:
        response = await ctx.planner.execute_plan(workspace_id, request.query)
        return response
    except Exception as e:
        logger.error("Workspace query error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge query failed: {str(e)}"
        )


@router.post("/api/workspaces/{workspace_id}/query/stream")
async def stream_workspace_query(
    workspace_id: str,
    request: KnowledgeQueryRequest,
    user: AuthUser = Depends(get_current_user),
    ctx: UserKnowledgeContext = Depends(get_current_user_context),
):
    """Stream one current planner stage at a time, followed by the answer contract."""
    enforce_workspace_ownership(user, workspace_id, ctx.repo)

    async def event_stream():
        updates: asyncio.Queue = asyncio.Queue()

        async def report(message: str) -> None:
            updates.put_nowait(("status", {"message": message}))
            # Let the response generator flush this status before a synchronous
            # retrieval or another CPU-bound specialist starts its next stage.
            await asyncio.sleep(0)

        async def execute() -> None:
            try:
                result = await ctx.planner.execute_plan(
                    workspace_id, request.query, on_progress=report
                )
                await updates.put(("result", result))
            except Exception:  # noqa: BLE001 - avoid streaming internal details
                logger.exception("Workspace query stream error")
                await updates.put(("error", {"message": "Knowledge query failed."}))

        task = asyncio.create_task(execute())
        try:
            while True:
                event, payload = await updates.get()
                yield _sse_event(event, payload)
                if event in {"result", "error"}:
                    break
        except asyncio.CancelledError:
            logger.info("Workspace query stream disconnected for workspace '%s'.", workspace_id)
            raise
        finally:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


