# TrustLens Render deployment review

This document describes the current repository configuration for a lightweight Render deployment. It is a configuration review, not proof that an existing Render dashboard has already applied every setting.

## Declared service configuration

`render.yaml` declares:

| Item | Current declaration |
|---|---|
| Service | Docker web service named `trustlens-api` |
| Build root | `backend` with `backend/Dockerfile` |
| Health check | `GET /health` |
| Plan | Render Free |
| Server shape | Single Uvicorn process from the Dockerfile |
| Auth mode | `prod` |
| Database | Free `trustlens-postgres` Postgres resource |
| Persistence binding | Database connection string mapped to `DATABASE_URL` |
| Browser origins | Local development, stable TrustLens Vercel origins, and a constrained preview regex |

The backend Docker image installs lightweight production requirements including FastAPI, Uvicorn, OpenAI, NumPy, PyJWT with cryptography, and `psycopg[binary]`. Local Torch, Transformers, spaCy, sentence-transformers, and FAISS are not part of the production requirements.

## Startup behavior

`backend/app/main.py` loads environment values before importing routes, creates the FastAPI app, configures CORS, and ensures schema inside lifespan. It does not load a local model, bulk corpus, or background worker at import time. OpenAI clients and specialist/planner objects are created lazily as needed.

This design is appropriate for a single-process free web service. It does not turn the service into a horizontally scalable worker system; concurrent request capacity and provider latency should be measured before making production load claims.

## Required Render dashboard settings

The following settings are environment-specific and cannot safely be committed:

1. `OPENAI_API_KEY` as a secret if provider-backed generation, embeddings, and verification are expected.
2. JWT verification material and optional issuer/audience settings that match the configured Clerk token issuer.
3. `DATABASE_URL` for a manually created service. Blueprint services receive this from the declared database binding after the Blueprint is applied.
4. Any extra CORS origin required for a custom frontend domain.

Never override the Docker command with an escaped `app.main:app` target. The backend Dockerfile owns the Uvicorn start command and expands Render's `PORT`.

## Persistence verification

After deployment, make an authenticated request to `GET /api/me/storage`.

```json
{
  "storage_backend": "postgres",
  "durable": true
}
```

is the expected durable result. If the result instead reports `sqlite` and `false`, the API is working in ephemeral local-storage mode. Documents from that mode can be lost when a free Render web service restarts, redeploys, or spins down. See [RENDER_PERSISTENCE_SETUP.md](RENDER_PERSISTENCE_SETUP.md).

## Browser connection checklist

If the Vercel frontend cannot reach Render:

1. Confirm Vercel was rebuilt after setting `VITE_API_URL` to the exact Render origin, without a trailing slash.
2. Confirm `/health` responds from the Render service.
3. Confirm `CORS_ORIGINS` or `CORS_ORIGIN_REGEX` permits the browser origin.
4. Check the browser Network tab for the first failed route and its status.
5. Confirm Clerk issues a token compatible with the configured auth settings.

Do not diagnose a CORS, auth, or missing database setting by changing backend source first. The deployed response and Render environment are the evidence.

## Free-plan limits

Render Free can spin down and has platform-specific service and database lifecycle limits. The first request after idle can be slower. Review current Render plan terms before using the deployment for long-lived data, backups, or uptime commitments.
