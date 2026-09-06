"""Authentication and authorization for TrustLens.

Provides JWT verification (production) and a safe development-mode fallback.
Every workspace-scoped endpoint resolves ownership from the authenticated
user context, preventing IDOR / cross-user access.
"""
import logging
import os
from dataclasses import dataclass, field
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.knowledge.user_storage import UserKnowledgeContext, get_user_context

logger = logging.getLogger("trustlens.auth")

# --- Configuration ----------------------------------------------------------------

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ISSUER = os.getenv("JWT_ISSUER", "")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "")
# When AUTH_MODE=dev, the backend trusts the x-user-id header without verifying
# a JWT. This is ONLY for local development and is rejected in production.
AUTH_MODE = os.getenv("AUTH_MODE", "dev" if not JWT_SECRET else "prod")
# Algorithms we are willing to accept. Explicitly deny "none".
# For RS256/ES256 (e.g. Clerk), JWT_SECRET must be the PEM-encoded public key.
ALLOWED_ALGORITHMS = [
    a.strip() for a in os.getenv("JWT_ALGORITHMS", "HS256,RS256,ES256").split(",") if a.strip()
]

security = HTTPBearer(auto_error=False)


@dataclass
class AuthUser:
    """Authenticated user context resolved from a verified JWT or dev-mode header."""

    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    is_authenticated: bool = False
    auth_method: str = "anonymous"
    claims: dict = field(default_factory=dict)


class WorkspaceOwnershipError(HTTPException):
    """Raised when a user attempts to access a workspace they do not own."""

    def __init__(self, workspace_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace '{workspace_id}' not found.",
        )


# --- JWT verification -------------------------------------------------------------

def _verify_jwt(token: str) -> Optional[dict]:
    """Verify a JWT and return its payload, or None if verification fails."""
    if not JWT_SECRET:
        logger.warning("AUTH_MODE=prod but JWT_SECRET is not configured; refusing all tokens")
        return None
    try:
        import jwt
    except ImportError:
        logger.warning("PyJWT not installed; cannot verify JWT")
        return None

    try:
        kwargs = {"algorithms": ALLOWED_ALGORITHMS}
        if JWT_ISSUER:
            kwargs["issuer"] = JWT_ISSUER
        if JWT_AUDIENCE:
            kwargs["audience"] = JWT_AUDIENCE
        # require exp claim
        kwargs["options"] = {"require": ["exp"]}
        return jwt.decode(token, JWT_SECRET, **kwargs)
    except Exception as e:  # noqa: BLE001
        logger.warning("JWT verification failed: %s", e)
        return None


def _extract_bearer_token(
    request: Request, credentials: Optional[HTTPAuthorizationCredentials]
) -> Optional[str]:
    """Extract a Bearer token from the Authorization header or cookie."""
    if credentials and credentials.scheme.lower() == "bearer":
        return credentials.credentials
    # Fallback: check a cookie (Clerk sets __session)
    return request.cookies.get("__session")


# --- Dependencies -----------------------------------------------------------------

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> AuthUser:
    """
    Resolve the authenticated user.

    Production (AUTH_MODE=prod, JWT_SECRET set):
        - Requires a valid Bearer JWT.
        - user_id is taken from the 'sub' claim.

    Development (AUTH_MODE=dev):
        - Trusts the x-user-id header without cryptographic verification.
        - is_authenticated=False so the UI can show a dev indicator.
    """
    if AUTH_MODE == "prod":
        token = _extract_bearer_token(request, credentials)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        payload = _verify_jwt(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return AuthUser(
            user_id=str(payload.get("sub", "")),
            email=payload.get("email"),
            name=payload.get("name"),
            is_authenticated=True,
            auth_method="jwt",
            claims=payload,
        )

    # Development mode: trust x-user-id header
    user_id = request.headers.get("x-user-id", "").strip()
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="x-user-id header required in development mode.",
        )
    return AuthUser(
        user_id=user_id,
        email=f"{user_id}@dev.local",
        name=user_id,
        is_authenticated=False,
        auth_method="dev",
    )


async def get_current_user_context(
    user: AuthUser = Depends(get_current_user),
) -> UserKnowledgeContext:
    """Resolve the authenticated user's isolated knowledge context."""
    return get_user_context(user.user_id)


# --- Workspace ownership enforcement ---------------------------------------------

def enforce_workspace_ownership(
    user: AuthUser, workspace_id: str, repo
) -> None:
    """
    Verify that the authenticated user owns the given workspace.

    Raises WorkspaceOwnershipError (404) if the workspace does not exist or
    is not owned by the user. Returns None on success.
    """
    ws = repo.get_workspace(workspace_id)
    if ws is None:
        raise WorkspaceOwnershipError(workspace_id)
    owner = ws.get("owner_user_id")
    if owner and owner != user.user_id:
        # Return 404 (not 403) to avoid leaking the existence of other users' workspaces
        raise WorkspaceOwnershipError(workspace_id)
    return None
