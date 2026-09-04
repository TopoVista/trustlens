"""
Per-User Hard Disk Storage Manager for TrustLens.
Ensures strict multi-tenant isolation by allocating dedicated SQLite databases
and file storage directories on the host hard disk for each user.
"""
import os
import re
import sqlite3
import logging
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

        # Initialize user's private SQLite schema on disk
        init_knowledge_schema(self.db_path)

        # Instantiate isolated repository and agents
        self.repo = KnowledgeRepository(db_path=self.db_path)
        self.repo.ensure_default_workspace()
        self.ingestion_agent = IngestionKnowledgeAgent(self.repo)
        self.planner = AnalysisPlanner(self.repo)

        logger.info(
            "Initialized user knowledge context for '%s' at: %s",
            self.user_id,
            self.db_path
        )


# In-memory registry of active user contexts to prevent recreating pools
_USER_CONTEXT_CACHE: Dict[str, UserKnowledgeContext] = {}


def get_user_context(user_id: Optional[str] = None) -> UserKnowledgeContext:
    """Thread-safe getter for a user's isolated knowledge context."""
    clean_id = sanitize_user_id(user_id)
    if clean_id not in _USER_CONTEXT_CACHE:
        _USER_CONTEXT_CACHE[clean_id] = UserKnowledgeContext(clean_id)
    return _USER_CONTEXT_CACHE[clean_id]
