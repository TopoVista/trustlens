import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables before importing routes.  Route imports resolve
# authentication configuration, so loading this afterwards silently made a
# local backend ignore AUTH_MODE/JWT values from backend/.env.  Do not let a
# checked-out .env override Render's actual service environment.
for env_path in [
    Path(__file__).resolve().parent.parent / ".env",
    Path(__file__).resolve().parents[2] / ".env"
]:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)

from app.api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("trustlens")

# Parse CORS origins from environment variable. The stable TrustLens frontend
# origins are always included as a deployment-safe fallback: a stale Render
# dashboard value must not silently block the production frontend's browser
# requests. Additional customer/local origins still come from CORS_ORIGINS.
_TRUSTLENS_FRONTEND_ORIGINS = {
    "http://localhost:5173",
    "http://localhost:3000",
    "https://trustlens.vercel.app",
    "https://trustlens-alpha.vercel.app",
}
cors_env = os.getenv("CORS_ORIGINS", "")
allowed_origins = sorted(
    _TRUSTLENS_FRONTEND_ORIGINS
    | {origin.strip().rstrip("/") for origin in cors_env.split(",") if origin.strip()}
)
# Optional, narrowly scoped support for Vercel preview deployments. Keep this
# empty unless preview URLs are desired; exact origins above remain preferred.
allowed_origin_regex = os.getenv("CORS_ORIGIN_REGEX", "").strip() or None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Explicit schema initialization for the default (shared) knowledge database.
    # Per-user databases initialize their own schema lazily on first access
    # (see UserKnowledgeContext). No heavy models or large datasets are loaded
    # here — the service starts with only the lightweight Python runtime.
    try:
        from app.knowledge.db import ensure_schema
        ensure_schema()
        logger.info("Default knowledge schema ensured.")
    except Exception:
        logger.exception("Failed to ensure default knowledge schema; "
                         "endpoints will retry initialization on demand.")
    logger.info("TrustLens API startup. Allowed CORS origins: %s", allowed_origins)
    yield
    logger.info("TrustLens API shutdown.")


app = FastAPI(
    title="TrustLens API",
    description="AI Reliability & RAG Claim Verification Engine",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_origin_regex=allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
