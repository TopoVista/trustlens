"""
Strict Per-User Hard Disk Isolation Tests for TrustLens.

Verifies that each authenticated user is allocated a dedicated, private
directory and SQLite database under backend/data/users/, and that no
knowledge (documents, claims, workspaces) can leak between users even when
a foreign workspace/document ID is known.

These tests exercise the exact on-disk layout used by the production API:
    backend/data/users/{sanitized_user_id}/trustlens_knowledge.db
    backend/data/users/{sanitized_user_id}/documents/
    backend/data/users/{sanitized_user_id}/cache/
"""
import asyncio
import os
import sqlite3
import sys
from pathlib import Path

import pytest

# Ensure backend package is in python path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.knowledge import user_storage as user_storage_mod
from app.knowledge.user_storage import (
    get_user_context,
    get_user_db_path,
    get_user_storage_dir,
    get_user_storage_stats,
    sanitize_user_id,
)

USER_ALPHA = "user_alpha"
USER_BETA = "user_beta"


@pytest.fixture(autouse=True)
def _isolated_test_users(tmp_path, monkeypatch):
    """
    Redirects every user partition under backend/data/users to an ephemeral
    temp directory and resets the in-memory context cache between tests. This
    keeps the real developer data untouched and avoids Windows file-lock
    issues (SQLite connections remain open across repository operations).
    """
    monkeypatch.setattr(user_storage_mod, "USERS_ROOT_DIR", tmp_path / "users")
    user_storage_mod._USER_CONTEXT_CACHE.clear()
    yield
    user_storage_mod._USER_CONTEXT_CACHE.clear()


def _count_rows(db_path: str, table: str) -> int:
    """Directly inspects the on-disk SQLite database, bypassing repositories."""
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()


# --- 1. User ID sanitization / filesystem safety ---

def test_sanitize_user_id_blocks_path_traversal():
    """'../../etc/passwd' style IDs must collapse to a flat single segment."""
    safe = sanitize_user_id("../../etc/passwd")
    assert "/" not in safe
    assert "\\" not in safe
    assert ".." not in safe

    # Legitimate Clerk-style IDs are preserved
    assert sanitize_user_id("user_2pQx9AbC123") == "user_2pQx9AbC123"

    # Empty / absent IDs fall back to the offline developer profile
    assert sanitize_user_id("") == "default_user"
    assert sanitize_user_id(None) == "default_user"


# --- 2. Dedicated directory & database per user ---

def test_each_user_gets_dedicated_directory_and_database():
    ctx_a = get_user_context(USER_ALPHA)
    ctx_b = get_user_context(USER_BETA)

    dir_a = get_user_storage_dir(USER_ALPHA)
    dir_b = get_user_storage_dir(USER_BETA)

    assert dir_a.is_dir()
    assert dir_b.is_dir()
    assert dir_a != dir_b
    # Physical paths must end in .../users/user_alpha and .../users/user_beta
    assert os.path.normpath(str(dir_a)).endswith(os.path.join("users", "user_alpha"))
    assert os.path.normpath(str(dir_b)).endswith(os.path.join("users", "user_beta"))

    # Expected per-user layout on the hard disk
    assert (dir_a / "documents").is_dir()
    assert (dir_a / "cache").is_dir()
    assert (dir_a / "trustlens_knowledge.db").exists()
    assert (dir_b / "trustlens_knowledge.db").exists()
    assert get_user_db_path(USER_ALPHA) != get_user_db_path(USER_BETA)

    # Automatic default-workspace provisioning is per-user and isolated
    ws_a = ctx_a.repo.list_workspaces()
    ws_b = ctx_b.repo.list_workspaces()
    assert len(ws_a) >= 1
    assert len(ws_b) >= 1
    assert ws_a[0]["id"] != ws_b[0]["id"]


# --- 3. Document A ingested into user_alpha is unreachable by user_beta ---

def test_documents_ingested_into_alpha_are_invisible_to_beta():
    alpha_ctx = get_user_context(USER_ALPHA)
    beta_ctx = get_user_context(USER_BETA)

    ws_alpha = alpha_ctx.repo.ensure_default_workspace()
    beta_ctx.repo.ensure_default_workspace()

    document_a = (
        "Acme Cloud achieved 99.99% availability in fiscal year 2025. "
        "Acme Cloud encrypts all data at rest using AES-256. "
        "The platform completed SOC 2 Type II certification in March 2025."
    )

    result = asyncio.run(
        alpha_ctx.ingestion_agent.ingest_content(
            workspace_id=ws_alpha,
            title="Acme Cloud Security Assessment",
            filename="acme_security.txt",
            raw_content=document_a,
            file_type="text",
            authority_level="HIGH",
        )
    )
    assert result["document_id"]
    assert result["claims_extracted"] >= 1

    # --- user_alpha's on-disk SQLite database holds the document + claims ---
    alpha_docs = alpha_ctx.repo.get_documents(ws_alpha)
    assert len(alpha_docs) == 1
    assert alpha_docs[0]["title"] == "Acme Cloud Security Assessment"

    alpha_claims = alpha_ctx.repo.get_claims(ws_alpha)
    assert len(alpha_claims) >= 1
    assert any("99.99%" in c["statement"] for c in alpha_claims)

    doc_a_id = alpha_docs[0]["id"]

    # Evaluate the physical database files directly on disk
    assert _count_rows(get_user_db_path(USER_ALPHA), "documents") == 1
    assert _count_rows(get_user_db_path(USER_ALPHA), "claims") >= 1

    # --- user_beta's on-disk SQLite database has ZERO traces of Document A ---
    assert _count_rows(get_user_db_path(USER_BETA), "documents") == 0
    assert _count_rows(get_user_db_path(USER_BETA), "claims") == 0

    # --- Even with the foreign workspace/document IDs, beta cannot resolve ---
    assert beta_ctx.repo.get_documents(ws_alpha) == []
    assert beta_ctx.repo.get_claims(ws_alpha) == []
    assert beta_ctx.repo.get_document(ws_alpha, doc_a_id) is None
    assert beta_ctx.repo.get_knowledge_graph(ws_alpha) == {"nodes": [], "edges": []}


# --- 4. Per-user storage metrics & document counts ---

def test_storage_stats_report_per_user_partition():
    alpha_ctx = get_user_context(USER_ALPHA)
    ws_alpha = alpha_ctx.repo.ensure_default_workspace()

    asyncio.run(
        alpha_ctx.ingestion_agent.ingest_content(
            workspace_id=ws_alpha,
            title="Endpoint Hardening",
            filename="hardening.txt",
            raw_content="The network segments all application traffic using zero trust policies.",
            file_type="text",
        )
    )

    stats_alpha = get_user_storage_stats(USER_ALPHA)
    stats_beta = get_user_storage_stats(USER_BETA)

    assert stats_alpha["user_id"] == USER_ALPHA
    assert stats_beta["user_id"] == USER_BETA
    assert "user_alpha" in stats_alpha["storage_path"]
    assert "user_beta" in stats_beta["storage_path"]
    assert stats_alpha["storage_path"] != stats_beta["storage_path"]

    # Alpha has 1 document; beta is untouched
    assert stats_alpha["document_count"] == 1
    assert stats_beta["document_count"] == 0
    assert stats_alpha["workspace_count"] >= 1
    assert stats_alpha["total_bytes"] > 0


# --- 5. API-level per-user routing via x-user-id header ---

def test_api_me_storage_isolated_per_user_header():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    r_alpha = client.get("/api/me/storage", headers={"x-user-id": "user_alpha"})
    assert r_alpha.status_code == 200
    body_alpha = r_alpha.json()
    assert body_alpha["user_id"] == "user_alpha"
    assert "user_alpha" in body_alpha["storage_path"]
    assert "document_count" in body_alpha

    r_beta = client.get("/api/me/storage", headers={"x-user-id": "user_beta"})
    assert r_beta.status_code == 200
    body_beta = r_beta.json()
    assert body_beta["user_id"] == "user_beta"
    assert "user_beta" in body_beta["storage_path"]

    # Workspace lists are disjoint between users
    ws_a = client.get("/api/workspaces", headers={"x-user-id": "user_alpha"}).json()
    ws_b = client.get("/api/workspaces", headers={"x-user-id": "user_beta"}).json()
    ids_a = {w["id"] for w in ws_a}
    ids_b = {w["id"] for w in ws_b}
    assert ids_a and ids_b
    assert ids_a.isdisjoint(ids_b)