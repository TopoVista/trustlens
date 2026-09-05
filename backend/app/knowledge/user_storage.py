"""
Per-User Hard Disk Storage Manager for TrustLens.
Ensures strict multi-tenant isolation by allocating dedicated SQLite databases
and file storage directories on the host hard disk for each user.
"""
import os
import re
import sqlite3
import logging
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Optional, Any

from app.knowledge.db import init_knowledge_schema
from app.knowledge.repository import KnowledgeRepository
from app.specialists.ingestion_agent import IngestionKnowledgeAgent
from app.planner.planner import AnalysisPlanner

logger = logging.getLogger("trustlens.user_storage")

BASE_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
USERS_ROOT_DIR = BASE_DATA_DIR / "users"


def sanitize_user_id(user_id: Optional[str]) -> str:
    """Sanitizes user ID to ensure safe filesystem path usage."""
    if not user_id or not user_id.strip():
        return "default_user"
    # Keep only alphanumeric, hyphens, and underscores
    clean = re.sub(r"[^a-zA-Z0-9_\-]", "_", user_id.strip())
    return clean[:64] if clean else "default_user"


def get_user_storage_dir(user_id: str) -> Path:
    """Returns and creates the dedicated hard disk directory for a user."""
    sanitized = sanitize_user_id(user_id)
    user_dir = USERS_ROOT_DIR / sanitized
    user_dir.mkdir(parents=True, exist_ok=True)
    (user_dir / "documents").mkdir(exist_ok=True)
    (user_dir / "cache").mkdir(exist_ok=True)
    return user_dir


def get_user_db_path(user_id: str) -> str:
    """Returns path to the user's isolated SQLite database."""
    user_dir = get_user_storage_dir(user_id)
    return str(user_dir / "trustlens_knowledge.db")


def get_user_storage_stats(user_id: str) -> Dict[str, Any]:
    """Calculates disk space usage and storage metrics for a specific user."""
    user_dir = get_user_storage_dir(user_id)
    total_bytes = 0
    file_count = 0

    for root, _, files in os.walk(user_dir):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total_bytes += os.path.getsize(fp)
                file_count += 1
            except OSError:
                pass

    db_path = get_user_db_path(user_id)
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

    # Read document counts from the user's isolated SQLite database
    document_count = 0
    workspace_count = 0
    claim_count = 0
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            document_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            workspace_count = conn.execute("SELECT COUNT(*) FROM workspaces").fetchone()[0]
            claim_count = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
            conn.close()
        except sqlite3.Error as e:
            logger.warning("Could not read counts for user '%s': %s", sanitize_user_id(user_id), e)

    return {
        "user_id": sanitize_user_id(user_id),
        "storage_path": str(user_dir),
        "total_bytes": total_bytes,
        "total_kb": round(total_bytes / 1024, 2),
        "total_mb": round(total_bytes / (1024 * 1024), 3),
        "db_bytes": db_size,
        "files_count": file_count,
        "document_count": document_count,
        "workspace_count": workspace_count,
        "claim_count": claim_count
    }


class UserKnowledgeContext:
    """Encapsulates a user's isolated repository, ingestion agent, and planner."""

    def __init__(self, user_id: str):
        self.user_id = sanitize_user_id(user_id)
        self.storage_dir = get_user_storage_dir(self.user_id)
        self.db_path = get_user_db_path(self.user_id)

        # Initialize user's private SQLite schema on disk (cheap, explicit)
        init_knowledge_schema(self.db_path)

        # Repository is lightweight (SQLite handle, no models) — keep eager.
        self.repo = KnowledgeRepository(db_path=self.db_path)
        self.repo.ensure_default_workspace()

        # Heavy orchestrators are constructed lazily on first use so that
        # endpoints like /health, /documents (read), /claims, /entities never
        # pay for planner/specialist instantiation (Stage 8 requirement).
        self._ingestion_agent: Optional[IngestionKnowledgeAgent] = None
        self._planner: Optional[AnalysisPlanner] = None

        logger.info(
            "Initialized user knowledge context for '%s' at: %s",
            self.user_id,
            self.db_path
        )

    @property
    def ingestion_agent(self) -> IngestionKnowledgeAgent:
        """Lazily constructed ingestion agent (per-user singleton)."""
        if self._ingestion_agent is None:
            self._ingestion_agent = IngestionKnowledgeAgent(self.repo)
        return self._ingestion_agent

    @property
    def planner(self) -> AnalysisPlanner:
        """Lazily constructed analysis planner (per-user singleton)."""
        if self._planner is None:
            self._planner = AnalysisPlanner(self.repo)
        return self._planner


# In-memory registry of active user contexts (bounded LRU to avoid unbounded
# growth across many distinct authenticated users on a 512 MB container).
_USER_CACHE_MAX_SIZE = 64
_USER_CONTEXT_CACHE: "OrderedDict[str, UserKnowledgeContext]" = OrderedDict()


def get_user_context(user_id: Optional[str] = None) -> UserKnowledgeContext:
    """Thread-safe getter for a user's isolated knowledge context (LRU-bounded)."""
    clean_id = sanitize_user_id(user_id)
    ctx = _USER_CONTEXT_CACHE.get(clean_id)
    if ctx is None:
        ctx = UserKnowledgeContext(clean_id)
        _USER_CONTEXT_CACHE[clean_id] = ctx
        if len(_USER_CONTEXT_CACHE) > _USER_CACHE_MAX_SIZE:
            # Evict least-recently-used context; its on-disk state is safe.
            _USER_CONTEXT_CACHE.popitem(last=False)
    else:
        _USER_CONTEXT_CACHE.move_to_end(clean_id)
    return ctx
