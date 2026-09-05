import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

# Load environment variables from .env file if present
for env_path in [
    Path(__file__).resolve().parent.parent / ".env",
    Path(__file__).resolve().parents[2] / ".env"
]:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("trustlens")

# Parse CORS origins from environment variable
cors_env = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
allowed_origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]


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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
