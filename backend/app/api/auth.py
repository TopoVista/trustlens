"""
Authentication & User Context Resolution for TrustLens.
Supports Clerk Session Tokens and X-User-Id headers with graceful
fallback for offline local development.
"""
import json
import base64
import logging
from typing import Optional
from pydantic import BaseModel
from fastapi import Request, Header, Depends

from app.knowledge.user_storage import (
    UserKnowledgeContext,
    get_user_context,
    sanitize_user_id,
    get_user_storage_stats
)

logger = logging.getLogger("trustlens.auth")


class AuthUser(BaseModel):
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    is_authenticated: bool = False


def _decode_jwt_unverified(token: str) -> dict:
    """Extracts payload claims from a JWT without external network verification."""
    try:
        parts = token.split(".")
        if len(parts) >= 2:
            padded = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
            decoded = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
            return json.loads(decoded)
    except Exception as e:
        logger.debug("Could not parse JWT token: %s", e)
    return {}


def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
) -> AuthUser:
    """
    Extracts authenticated user from Clerk headers.
    Checks:
      1. X-User-Id header
      2. Authorization: Bearer <clerk_token>
      3. Defaults to 'default_user'
    """
    # 1. Direct X-User-Id header (set by frontend with Clerk user.id)
    if x_user_id and x_user_id.strip():
        clean_id = sanitize_user_id(x_user_id)
        return AuthUser(
            user_id=clean_id,
            is_authenticated=True
        )

    # 2. Bearer JWT
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        payload = _decode_jwt_unverified(token)
        sub = payload.get("sub")
        if sub:
            clean_id = sanitize_user_id(sub)
            return AuthUser(
                user_id=clean_id,
                email=payload.get("email") or payload.get("primary_email_address"),
                name=payload.get("name") or payload.get("first_name"),
                is_authenticated=True
            )

    # 3. Fallback for offline development / guest session
    return AuthUser(
        user_id="default_user",
        email=None,
        name="Local User",
        is_authenticated=False
    )


def get_current_user_context(
    current_user: AuthUser = Depends(get_current_user)
) -> UserKnowledgeContext:
    """
    FastAPI dependency that resolves the dedicated, isolated
    UserKnowledgeContext on the host hard disk for the calling user.
    """
    return get_user_context(current_user.user_id)
