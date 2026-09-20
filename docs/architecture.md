# TrustLens architecture

## Purpose

TrustLens turns a user's own source material into a reviewable evidence workspace. Its architecture keeps identity and ownership, persistent knowledge records, and answer-to-evidence analysis distinct.

```text
React SPA
  | workspace API calls; Clerk bearer token when configured
  v
FastAPI routes ------------------------> auth and ownership checks
  |                                           |
  +--> User knowledge context               verified user identity
  |       |
  |       +--> repository --> SQLite locally / Postgres with DATABASE_URL
  |       +--> ingestion specialist --> chunks, claims, entities, events
  |       +--> planner --> selected in-process specialists --> answer contract
  |
  +--> optional OpenAI provider boundary for generation, embeddings, NLI
```

## Frontend

`frontend/src/App.jsx` is the client composition root. It configures the API identity context, loads workspaces, and refreshes health, documents, discoveries, entities, timelines, and rules when the active workspace changes. Individual views are presentation-focused; `src/api.js` owns the HTTP contract.

The UI workflow is: select or create a workspace, ingest text-based source material with authority, refresh the source record, ask a question, and inspect synthesis, claims, evidence, conflicts, and unresolved items.

The workspace query stream uses a POST response with `text/event-stream`.
Planner callbacks report the current completed or active stage, and the client
shows only the latest line while it waits for the final `result` event. This is
not simulated progress; the messages are emitted at the planner's retrieval,
claim, evidence, intent-specific, synthesis, and answer-packaging stages.

The client normalizes confidence for display because legacy and workspace responses can use different scales. A value in `[0, 1]` becomes a percentage; a value already over `1` is treated as a percentage. Both forms are clamped to `[0, 100]`.

## API and identity

`backend/app/main.py` loads environment values before routes import authentication configuration, configures CORS, and ensures schema during FastAPI lifespan. `backend/app/api/auth.py` validates signed production JWTs and gives workspace-scoped routes an authenticated identity. `AUTH_MODE=dev` is a local development convenience; `AUTH_MODE=prod` requires a verified Bearer token and derives identity from its subject claim.

Every workspace operation performs an ownership check. A client cannot obtain another user's workspace merely by guessing its ID.

## Knowledge records and persistence

`backend/app/knowledge/repository.py` owns data operations for workspaces, documents, chunks, chunk embeddings, claims, evidence links, entities, relationships, timeline events, semantic rules, health summaries, and proactive discoveries.

`backend/app/knowledge/db.py` makes the repository portable:

- Without `DATABASE_URL`, it opens SQLite. Local user contexts receive a sanitized, user-specific database path and SQLite WAL mode is enabled.
- With `DATABASE_URL`, it opens Postgres through `psycopg`. A small adapter allows the same repository query interface to use Postgres parameters.
- Schema initialization uses `CREATE TABLE IF NOT EXISTS` plus additive migrations so existing local data is not discarded on upgrade.

The service has durable Render storage only when `DATABASE_URL` is present in the running service. The storage endpoint exposes this condition directly.

## Ingestion and analysis

The document route accepts a validated title, filename, source text, file type, and authority level. The ingestion specialist persists the source and its chunks, then extracts claims, entities, and temporal anchors where available. The response includes `document_id`, `authority_level`, `chunks_count`, and ingestion status so the frontend can update its source register.

For a question, the planner selects applicable specialist capabilities from the registry rather than running every capability by default. Relevant specialists handle claim detection, evidence grounding, entity extraction, timeline analysis, contradiction detection, gap analysis, comparison, pattern hunting, data analysis, and synthesis. They run as lightweight in-process classes, not as separate services or background workers.

The optional provider layer in `backend/app/llm` and `backend/app/models` creates OpenAI clients lazily. The production dependency set deliberately excludes local Torch, Transformers, spaCy, sentence-transformers, and FAISS runtime paths. Fallback behavior must be described as degraded operation, not as equivalent provider-backed verification.

## Intelligence graph projection

Canonical `documents`, `chunks`, `claims`, `evidence`, `entities`,
`relationships`, `events`, and dataset-profile records remain the source of
truth. `graph_nodes` and `graph_edges` are an additive, workspace-scoped
projection built after ingestion (and lazily for pre-existing workspaces).
Every graph edge includes confidence, method/provenance, source document or
chunk when available, and a human-readable explanation.

The browser requests `GET /api/workspaces/{id}/graph` once per workspace
refresh, then performs ordinary type, relation, confidence, and status filters
client-side. Sigma renders the filtered projection; Graphology owns the local
graph representation and interaction state. Node, neighbor, and path endpoints
repeat ownership validation server-side, so a graph node ID cannot cross a
workspace boundary.

Relationship extraction is conservative. Explicit source language can form
`DEPENDS_ON`, `AFFECTS`, `CONTRIBUTES_TO`, or `CAUSES`; simple co-occurrence is
only a low-confidence `ASSOCIATED_WITH` edge. Dataset correlations are stored
as `CORRELATED_WITH` with coefficient/sample metadata and are explicitly not
causal claims.

Workspace verification adds deterministic numeric and temporal checks beside
NLI. Both return provenance and remain distinguishable from provider-backed
NLI; the resulting trust-support score is an evidence support signal, not a
probability that a statement is objectively true.

## Deployment boundaries

The Render Docker service and Postgres Blueprint resource are described in `render.yaml`. Vercel deploys the independent Vite app from `frontend` and requires `VITE_API_URL` at build time. Browser success depends on all of these being aligned:

1. Vercel was built with the intended backend URL.
2. Render CORS permits that Vercel origin.
3. Render has the right auth configuration for the Clerk token issuer.
4. Render has `DATABASE_URL` when durable source retention is required.

See [RENDER_PERSISTENCE_SETUP.md](RENDER_PERSISTENCE_SETUP.md) for the operational persistence check.
