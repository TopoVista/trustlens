# TrustLens backend

The backend is a FastAPI application for workspace-scoped document ingestion,
evidence-oriented analysis, and lightweight dataset analytics. It is designed
to run as one Dockerized Uvicorn process on Render without local ML model
servers or background workers.

## Run locally

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

Use `GET /health` to confirm the service is alive and `GET /health/ready` for
a readiness probe.

## Runtime configuration

| Variable | Purpose |
|---|---|
| `AUTH_MODE` | `prod` requires a verified Bearer JWT. `dev` permits a local `x-user-id` test header. |
| `JWT_ALGORITHMS` | Allowed signing algorithms. `none` is not accepted. |
| `JWT_SECRET`, `JWT_ISSUER`, `JWT_AUDIENCE` | Production JWT verification settings as applicable to the token issuer. |
| `CORS_ORIGINS`, `CORS_ORIGIN_REGEX` | Browser origins permitted to call the API. |
| `DATABASE_URL` | Enables durable Postgres. Without it, local development uses per-user SQLite. |
| `OPENAI_API_KEY` | Enables provider-backed generation, embeddings, and verification paths. |
| `OPENAI_MODEL`, `OPENAI_EMBEDDING_MODEL`, `OPENAI_NLI_MODEL` | Optional provider model selection. |
| `NLI_THRESHOLD`, `RETRIEVAL_K`, `CLAIM_RETRIEVAL_K` | Verification and retrieval tuning. |

Do not place any secret in source control or a browser-exposed `VITE_` variable.

## Key routes

| Route | Purpose |
|---|---|
| `GET /health`, `GET /health/ready`, `GET /health/memory` | Service probes and lightweight diagnostics. |
| `GET /api/me`, `GET /api/me/storage` | Caller identity metadata and storage status. |
| `GET/POST /api/workspaces` | List or create owner-scoped workspaces. |
| `GET /api/workspaces/{id}/health` | Workspace document, claim, graph, and gap summary. |
| `POST/GET /api/workspaces/{id}/documents` | Ingest or list workspace documents. Ingestion returns document ID and authority. |
| `GET /api/workspaces/{id}/discoveries` | Cross-source discovery and review signals. |
| `GET /api/workspaces/{id}/claims`, `/entities`, `/timeline` | Read the enriched evidence record. |
| `GET/POST /api/workspaces/{id}/rules` | Read or add workspace verification rules. |
| `POST /api/workspaces/{id}/query` | Run an evidence-grounded workspace analysis. |
| `/datasets/*` | Lightweight server API for uploading, profiling, exploring, and deleting tabular datasets. |

Legacy `/answer`, `/analyze`, `/api/assess`, and `/api/ask` endpoints remain
for compatibility. The active React product uses the workspace routes.

## Storage behavior

`app/knowledge/db.py` chooses the storage implementation based on
`DATABASE_URL`. With no URL, `user_storage.py` creates a sanitized user
directory with a private SQLite database. With a URL, the shared repository
API uses Postgres and keeps access isolation at the `owner_user_id` workspace
boundary. Check `/api/me/storage` rather than assuming the deployment mode.

## Tests

From repository root:

```powershell
pytest tests -q
```

The suite covers authentication and ownership, persistence selection, routes,
agents and planner dispatch, pipeline behavior, CORS, analytics, and security.
