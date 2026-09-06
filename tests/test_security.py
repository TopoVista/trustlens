"""
Security hardening tests for TrustLens.

Verifies:
1. JWT signature verification (production mode) - forged, expired, wrong-signature,
   and 'none'-algorithm tokens are all rejected; valid tokens are accepted.
2. Development-mode authentication (x-user-id) is properly scoped and required.
3. Workspace ownership enforcement prevents IDOR / cross-user access.
"""
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
import jwt as pyjwt

# Ensure backend package is in python path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import app.api.auth as auth_mod
from app.api.auth import AuthUser, WorkspaceOwnershipError, enforce_workspace_ownership
from app.knowledge import user_storage as user_storage_mod
from app.main import app

client = TestClient(app)

SECRET = "test-secret-key-for-unit-tests-0123456789"
OTHER_SECRET = "different-key-for-forged-tokens-0123456789"


def _make_token(payload: dict, secret: str = SECRET, algorithm: str = "HS256") -> str:
    """Create a signed JWT for testing."""
    return pyjwt.encode(payload, secret, algorithm=algorithm)


def _valid_payload(sub: str = "jwt_user_alpha") -> dict:
    return {
        "sub": sub,
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
        "email": f"{sub}@example.com",
    }


@pytest.fixture(autouse=True)
def _isolated_users(tmp_path, monkeypatch):
    """Redirect per-user storage to a temp dir and reset caches between tests."""
    monkeypatch.setattr(user_storage_mod, "USERS_ROOT_DIR", tmp_path / "users")
    user_storage_mod._USER_CONTEXT_CACHE.clear()
    yield
    user_storage_mod._USER_CONTEXT_CACHE.clear()


@pytest.fixture
def prod_mode(monkeypatch):
    """Force production JWT authentication for the duration of a test."""
    monkeypatch.setattr(auth_mod, "AUTH_MODE", "prod")
    monkeypatch.setattr(auth_mod, "JWT_SECRET", SECRET)
    yield

@pytest.fixture
def prod_mode_no_secret(monkeypatch):
    """AUTH_MODE=prod but JWT_SECRET unset -> must fail closed (reject all)."""
    monkeypatch.setattr(auth_mod, "AUTH_MODE", "prod")
    monkeypatch.setattr(auth_mod, "JWT_SECRET", "")
    yield


def test_prod_mode_without_configured_secret_fails_closed(prod_mode_no_secret):
    """If AUTH_MODE=prod but JWT_SECRET is missing, every request is rejected
    (never fall back to trusting x-user-id)."""
    resp = client.get("/api/workspaces", headers={"x-user-id": "attacker"})
    assert resp.status_code == 401
    resp = client.get("/api/workspaces")
    assert resp.status_code == 401


# --- 1. Development mode authentication ------------------------------------


def test_dev_mode_requires_x_user_id_header():
    resp = client.get("/api/workspaces")
    assert resp.status_code == 401
    assert "x-user-id" in resp.json().get("detail", "").lower()


def test_dev_mode_accepts_x_user_id_header():
    resp = client.get("/api/workspaces", headers={"x-user-id": "dev_user"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# --- 2. JWT verification (production mode) ---------------------------------


def test_prod_mode_requires_bearer_token(prod_mode):
    resp = client.get("/api/workspaces")
    assert resp.status_code == 401


def test_prod_mode_accepts_valid_token(prod_mode):
    token = _make_token(_valid_payload())
    resp = client.get("/api/workspaces", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_prod_mode_rejects_forged_signature(prod_mode):
    token = _make_token(_valid_payload(), secret=OTHER_SECRET)
    resp = client.get("/api/workspaces", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_prod_mode_rejects_expired_token(prod_mode):
    payload = _valid_payload()
    payload["exp"] = int(time.time()) - 60  # expired
    token = _make_token(payload)
    resp = client.get("/api/workspaces", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_prod_mode_rejects_none_algorithm(prod_mode):
    token = _make_token(_valid_payload(), secret=None, algorithm="none")
    resp = client.get("/api/workspaces", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_prod_mode_rejects_missing_exp_claim(prod_mode):
    payload = {"sub": "jwt_user_alpha"}  # no exp claim
    token = _make_token(payload)
    resp = client.get("/api/workspaces", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_prod_mode_user_id_comes_from_token_sub(prod_mode):
    token = _make_token(_valid_payload(sub="jwt_user_alpha"))
    resp = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == "jwt_user_alpha"
    assert body["is_authenticated"] is True
    assert body["auth_method"] == "jwt"


def test_dev_mode_user_is_marked_unauthenticated():
    resp = client.get("/api/me", headers={"x-user-id": "dev_user"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == "dev_user"
    assert body["is_authenticated"] is False
    assert body["auth_method"] == "dev"


# --- 3. Workspace ownership enforcement (IDOR prevention) -------------------


def test_create_workspace_records_owner():
    resp = client.post(
        "/api/workspaces",
        json={"name": "Alpha Private", "description": "secret space"},
        headers={"x-user-id": "user_alpha"},
    )
    assert resp.status_code == 200
    ws = resp.json()
    # Verify ownership is persisted via the repo
    ctx = user_storage_mod.get_user_context("user_alpha")
    stored = ctx.repo.get_workspace(ws["id"])
    assert stored["owner_user_id"] == "user_alpha"


def test_list_workspaces_scoped_to_owner():
    client.post(
        "/api/workspaces",
        json={"name": "Alpha's space"},
        headers={"x-user-id": "user_alpha"},
    )
    client.post(
        "/api/workspaces",
        json={"name": "Beta's space"},
        headers={"x-user-id": "user_beta"},
    )
    alpha_ids = {w["id"] for w in client.get("/api/workspaces", headers={"x-user-id": "user_alpha"}).json()}
    beta_ids = {w["id"] for w in client.get("/api/workspaces", headers={"x-user-id": "user_beta"}).json()}
    assert alpha_ids
    assert beta_ids
    assert alpha_ids.isdisjoint(beta_ids)


def test_cross_user_workspace_access_returns_404():
    """IDOR: user_beta must not read or query user_alpha's workspace."""
    created = client.post(
        "/api/workspaces",
        json={"name": "Alpha private docs"},
        headers={"x-user-id": "user_alpha"},
    ).json()
    ws_id = created["id"]

    # Every workspace-scoped read/query from another user must 404
    for method, path in [
        ("get", f"/api/workspaces/{ws_id}/health"),
        ("get", f"/api/workspaces/{ws_id}/discoveries"),
        ("get", f"/api/workspaces/{ws_id}/documents"),
        ("get", f"/api/workspaces/{ws_id}/claims"),
        ("get", f"/api/workspaces/{ws_id}/entities"),
        ("get", f"/api/workspaces/{ws_id}/timeline"),
        ("get", f"/api/workspaces/{ws_id}/rules"),
        ("post", f"/api/workspaces/{ws_id}/rules"),
        ("post", f"/api/workspaces/{ws_id}/query"),
    ]:
        kwargs = {"headers": {"x-user-id": "user_beta"}}
        if method == "post" and path.endswith("/query"):
            kwargs["json"] = {"query": "What is inside?"}
        elif method == "post" and path.endswith("/rules"):
            kwargs["json"] = {"rule_type": "constraint", "rule_key": "k", "rule_value": "v"}
        resp = getattr(client, method)(path, **kwargs)
        assert resp.status_code == 404, f"{method.upper()} {path}: {resp.status_code} {resp.text}"


def test_workspace_owner_can_access_own_workspace():
    created = client.post(
        "/api/workspaces",
        json={"name": "Alpha docs"},
        headers={"x-user-id": "user_alpha"},
    ).json()
    ws_id = created["id"]
    resp = client.get(f"/api/workspaces/{ws_id}/health", headers={"x-user-id": "user_alpha"})
    assert resp.status_code == 200


def test_enforce_ownership_helper_rejects_foreign_owner(tmp_path):
    """Direct unit test of the ownership check (shared-DB scenario)."""
    from app.knowledge.db import ensure_schema
    from app.knowledge.repository import KnowledgeRepository

    db_path = str(tmp_path / "shared.db")
    ensure_schema(db_path)
    repo = KnowledgeRepository(db_path=db_path)
    ws = repo.create_workspace("Owner alpha ws", owner_user_id="alpha")

    # Foreign user must be rejected with 404 (no existence leakage)
    with pytest.raises(WorkspaceOwnershipError):
        enforce_workspace_ownership(AuthUser(user_id="beta"), ws["id"], repo)

    # Owner passes
    enforce_workspace_ownership(AuthUser(user_id="alpha"), ws["id"], repo)

    # Nonexistent workspace raises
    with pytest.raises(WorkspaceOwnershipError):
        enforce_workspace_ownership(AuthUser(user_id="alpha"), "ws_missing", repo)


def test_enforce_ownership_helper_backfills_legacy_workspaces(tmp_path):
    """Legacy workspaces without an owner are accessible to the checking user.

    Legacy rows created before the owner_user_id migration have a NULL owner.
    The enforcement helper treats NULL owner as owned by the first caller so
    existing deployments are not locked out, while NEW workspaces always carry
    an explicit owner.
    """
    from app.knowledge.db import ensure_schema
    from app.knowledge.repository import KnowledgeRepository

    db_path = str(tmp_path / "legacy.db")
    ensure_schema(db_path)
    repo = KnowledgeRepository(db_path=db_path)
    ws = repo.create_workspace("Legacy ws")  # no owner_user_id (legacy call path)

    # No owner -> allowed for the checking user
    enforce_workspace_ownership(AuthUser(user_id="alpha"), ws["id"], repo)
        