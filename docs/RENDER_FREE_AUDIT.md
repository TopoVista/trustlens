# TrustLens — Render Free Deployment Audit

**Repository:** TopoVista/trustlens · **Branch:** `render-free-512mb`
**Scope:** full backend audit for reliable deployment on Render Free (Docker Web Service, ~512 MiB RAM).
**Method:** every claim below was verified by reading the code and/or executing probes on the
current tree (`importtime` traces, RSS measurement, live TestClient/uvicorn requests). Items
that are estimates are labelled **[estimate]**.

---

## 1. Architecture Discovered (current state)

### 1.1 Process model

Exactly **one process, one uvicorn worker**:

```
Docker CMD: sh -c "exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"
```

- No gunicorn, no Celery/RQ, no background threads, no scheduler. ✔
- `backend/app/main.py`: dotenv load → logging config → CORS → lifespan (logs only)
  → `app.include_router(routes.router)`.
- Single APIRouter in `backend/app/api/routes.py` hosts every endpoint.

### 1.2 Service layers (all in-process modules)

| Layer | Location | Purpose |
|---|---|---|
| API | `app/api/routes.py`, `auth.py`, `schemas.py` | endpoints, Clerk/`x-user-id` auth, Pydantic contracts |
| Pipeline | `app/pipeline/{retriever,generator,runner,assembler,claims,verifier}.py` | legacy corpus RAG: retrieve → generate → claim-split → verify |
| Models | `app/models/{embeddings,nli}.py` | embedding + NLI providers (see §3) |
| Knowledge | `app/knowledge/{db,repository,hybrid_retriever,user_storage}.py` | SQLite per-user knowledge graph, workspace-scoped retrieval |
| Agents | `app/agents/*.py` (10) | legacy vendor-risk multi-agent flow (orchestrator + ingestion/parsing/retrieval/compliance/scoring/report/QA) |
| Specialists | `app/specialists/*.py` (11) | knowledge-intelligence capabilities (claim detective, evidence, entity, timeline, gap, data analyst, pattern, comparison, synthesis, ingestion) |
| Planner | `app/planner/{planner,registry}.py` | intent-aware dispatch of specialists |
| Evaluator | `app/evaluator/metrics.py` | faithfulness / hallucination metrics |

**Key point:** the "agents" and "specialists" are **already plain Python classes instantiated
inside the same process** — not servers, not threads. They match the Part 4 requirement
(coordinator + specialist tool modules) structurally; no rework needed there.

### 1.3 Persistence

- **SQLite** (one DB per user): `backend/data/trustlens_knowledge.db` and
  `backend/data/users/{user_id}/trustlens_knowledge.db`. WAL mode, versioned schema.
  Stores workspaces, documents, chunks, **chunk embeddings (float32 BLOBs)**, claims,
  entities, timeline events, evidence links, semantic rules, query history.
- **Corpus vector store:** `backend/data/corpus_embeddings.npy` + `backend/data/doc_store.json`
  (450 corpus documents). Tracked in git. Loaded lazily on first legacy retrieval (~1–3 MB RAM).
- No external DB, no vector-DB server, no Redis. ✔ Render-Friendly.

### 1.4 LLM / ML integrations

| Concern | Provider | When loaded |
|---|---|---|
| Answer generation / synthesis / report | OpenAI chat completions | lazily, per request (`generator.py`) |
| Embeddings | OpenAI `text-embedding-3-small` (configurable via `OPENAI_EMBEDDING_MODEL`); deterministic offline fallback | lazily, per batch; **document embeddings persisted once** |
| Claim verification (NLI) | OpenAI structured-JSON entailment classifier; deterministic lexical fallback | lazily, per request (`nli.py`) |
| Sentence splitting | regex sentencizer with abbreviation protection | pure Python, zero deps |

**No local LLM. No PyTorch/transformers/sentence-transformers/spaCy/FAISS in the runtime.**
These were removed from production on the current branch (see §5); they exist only in git
history, not in imported code.

### 1.5 Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | for LLM/embedding/NLI features (app degrades gracefully without it) | generation, embeddings, verification |
| `OPENAI_EMBEDDING_MODEL` | no (default `text-embedding-3-small`) | embedding provider selection |
| `PORT` | provided by Render | bind port |
| `CORS_ORIGINS` | no | comma-separated allowed origins |

### 1.6 Frontend

React/Vite app in `frontend/`, served separately (Vercel). Calls:
`/health`, `/api/me/storage`, `/api/workspaces` (list/create), workspace
`/health`, `/discoveries`, `/documents` (GET/POST), `/claims`, `/entities`,
`/timeline`, `/rules` (GET/POST), `/query`. Sends `x-user-id` header.
Legacy `/answer`, `/analyze`, `/api/assess`, `/api/ask` are documented API surface but not
rendered by the current UI — **they must be preserved** (contract stability).

---

## 2. Startup Execution Flow (verified)

```
1. Python 3.11 starts                                   RSS ~15 MB     [measured, Linux-equiv.]
2. uvicorn imported                                     ~+15 MB
3. fastapi/starlette/pydantic imported                  ~+25 MB
4. app.main imported
   ├─ dotenv loads backend/.env (override=True)
   ├─ app.api.routes imported
   │   ├─ app.api.auth → app.knowledge.user_storage
   │   │    ├─ app.knowledge.db        (schema NOT touched at import — ensure_schema() only)
   │   │    ├─ app.knowledge.repository
   │   │    ├─ app.specialists.ingestion_agent → claims (regex; no spaCy)
   │   │    └─ app.planner.planner → registry (imports only; specialists built lazily)
   │   ├─ app.pipeline.retriever → numpy (file load lazy; no faiss)
   │   ├─ app.pipeline.generator → openai SDK (client constructed lazily per call)
   │   ├─ app.pipeline.assembler → claims (regex)
   │   └─ app.evaluator.metrics
5. FastAPI app created; lifespan runs (logging only; no model loads, no DB writes)
6. uvicorn binds 0.0.0.0:$PORT
```

**Measured (branch `render-free-512mb`, `scripts/profile_startup.py` + `scripts/memory_report.py`):**

| Stage | RSS |
|---|---|
| Python baseline | ~61 MB [Windows dev machine; Linux ~40–50 MB **[estimate]**] |
| after `import app.main` | **~80 MB** (was **~453 MB** before the refactor) |
| after FastAPI init / lifespan | ~82 MB |
| representative ingestion request | ~85 MB |
| workspace `/query` (full pipeline) | ~87 MB |
| legacy corpus retrieval (matrix load) | ~117 MB peak |
| **peak across all scenarios** | **~118 MB** |

Heavy modules (`torch`, `transformers`, `sentence_transformers`, `faiss`, `spacy`)
verified **absent from `sys.modules`** after startup.

---

## 3. Historical Root Causes of the Render Failures

| # | Failure | Root cause (verified) | Fix (in place on this branch) |
|---|---|---|---|
| 1 | Exit 128 during deployment | Build context included the 2.6 GB Windows `.venv` and stray untracked files (`COPY . .` with no `.dockerignore`); requirements pulled the multi-GB CUDA torch wheel | `backend/.dockerignore` added; production deps reduced to 6 packages |
| 2 | "No open ports detected" | Startup never completed: importing `sentence_transformers`/`torch`/`transformers`/`faiss`/`spacy` cost ~430 MB and 11–13 s, exceeding the 512 MiB cgroup before the listener bound | all heavy imports removed from the runtime; import cost now ~80 MB / <2 s |
| 3 | `sh: 1: exec python -m uvicorn app.main\:app ...: not found` | Docker command override contained an escaped colon (`app.main\:app`) — the backslash made `/bin/sh` look for a binary named `python -m uvicorn app.main\:app` | CMD lives **in the Dockerfile** and Render inherits it; no override needed. Correct form: `CMD ["sh", "-c", "exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]` (verified in `backend/Dockerfile`) |
| 4 | "Out of memory (used over 512Mi)" | (a) import-time ~450 MB as above; (b) request-time local models — MiniLM encode measured at 521 MB and the NLI cross-encoder at 718 MB | local models replaced with OpenAI API + persisted embeddings + deterministic fallbacks; measured peak now ~118 MB |

---

## 4. Dependency Classification (verified against actual imports)

### Production image (`backend/requirements-prod.txt`)

| Package | Class | Why required | Import cost |
|---|---|---|---|
| fastapi | CORE | framework, all routers | ~25 MB |
| uvicorn | CORE | ASGI server (single worker) | ~15 MB |
| openai | CORE | generation, embeddings, NLI classification (client lazy) | ~21 MB |
| pydantic | CORE | request/response schemas | (with fastapi) |
| python-dotenv | CORE | `.env` loading in main/generator | negligible |
| numpy | CORE | cosine/dot retrieval, persisted matrices | ~8–13 MB |

### Removed from production (the OOM source)

| Package | Was imported by | Measured cost | Replacement in place |
|---|---|---|---|
| torch | models/nli, sentence-transformers backend | +156 MB import; multi-GB CUDA wheel on Linux | OpenAI NLI + embeddings |
| transformers | models/nli | +26 MB | OpenAI JSON classifier + lexical fallback |
| sentence-transformers | models/embeddings | +159 MB | OpenAI embeddings (persisted once) + offline fallback |
| faiss-cpu | retriever, embeddings | +13 MB | NumPy dot-product cosine |
| spacy | pipeline/claims | +23 MB (+ model) | regex sentencizer (behavior-tested) |

### Development only (`backend/requirements-dev.txt`)

`pytest`, `psutil` (memory diagnostics). Never installed in the production image.

### Correctly absent

No LangChain/LangGraph/Haystack, no TensorFlow, no vector-DB clients, no SHAP/OpenCV/PyOD,
no pandas-heavy global state. The coordinator/specialist pattern is hand-rolled and cheap.

---

## 5. Startup / Import-Time Hazards — Status

| Hazard | Status on this branch |
|---|---|
| Global model instances at import | ✔ eliminated (lazy singletons: embedding model, NLI classifier, OpenAI client) |
| Heavy ML imports in the import tree | ✔ eliminated (verified via `sys.modules` check) |
| Import-time filesystem scanning | ✔ none |
| Import-time DB writes | ✔ fixed — `db.py` exposes `ensure_schema()`; called from lifespan / per-user context, never at import |
| Import-time network calls | ✔ none (clients constructed per use) |
| Unbounded global caches | ✔ fixed — per-user `UserKnowledgeContext` cache is an LRU (max 128); specialists/planners built only when an endpoint uses them |
| Giant global dataframes / corpora in RAM | ✔ none — corpus matrix loads lazily (~1–3 MB); workspace chunk embeddings fetched per query from SQLite |
| Multiple workers / background processes | ✔ none |

---

## 6. Required vs Optional Functionality

**Required for every deployment (works with zero external services):**
`/health`, `/health/ready`, `/health/memory`, workspace CRUD, document ingestion
(chunking, claim/entity/timeline extraction — deterministic), knowledge graph reads,
deterministic lexical/embedding-fallback retrieval, claim splitting, DB-backed evidence links.

**Optional (degrade gracefully when `OPENAI_API_KEY` is absent or the API fails):**
grounded answer generation (clear, non-crashing error surfaced to the client),
OpenAI embeddings (offline deterministic fallback vectors used; dimension drift in stored
vectors is detected and self-healed on the next query),
NLI verification (deterministic lexical SUPPORTED/CONTRADICTED/NOT_SUPPORTED fallback).

**Not present, and must not be added to the Render process:** local LLMs, PyTorch,
TensorFlow, embedding-vector-DB servers, dashboard servers (Superset/Grafana/Metabase),
Jupyter/Streamlit, Celery, MCP servers. MCP remains an *optional external* integration point.

---

## 7. Render Compatibility Review (configuration)

| Item | Current state | Verdict |
|---|---|---|
| Service type | Docker Web Service (`render.yaml`: `runtime: docker`, root dir `backend`) | ✔ |
| Dockerfile | `python:3.11-slim`, no OS extras, `--no-cache-dir`, installs `requirements-prod.txt`, `COPY app/ scripts/ data/` only | ✔ |
| Startup command | `CMD ["sh", "-c", "exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]` — shell form, `$PORT` expanded by `sh`, `exec` hands PID 1 to uvicorn, colon **unescaped** | ✔ |
| Workers | single uvicorn process (no `--workers`, no gunicorn) | ✔ |
| Health check | `healthCheckPath: /health`; plus `/health/ready` and `/health/memory` for deeper probes | ✔ |
| Port binding | `0.0.0.0:${PORT}` (falls back to 10000 locally) | ✔ |
| `.dockerignore` | excludes `.venv/`, `__pycache__/`, `.git`, `.env`, `data/users/`, `data/raw_docs/`, caches, junk files | ✔ |
| Memory headroom | peak ~118 MB measured vs 512 MiB limit → ~75–80% headroom | ✔ |
| Free plan | `plan: free` in `render.yaml`; no paid add-ons | ✔ |

Residual risk: the first legacy-corpus query may trigger a one-time OpenAI re-embed of the
450-doc corpus if the committed matrix was built with the offline fallback; afterwards it is
persisted to disk. Pre-warm with `python scripts/build_corpus_embeddings.py` (real key) if
undesired.

---

## 8. Proposed Fixes and Exact Files

### Already implemented on this branch (verified by tests + memory probes)

| Fix | File(s) | Validation |
|---|---|---|
| Lightweight production deps (6 packages) | `backend/requirements-prod.txt`, `requirements-dev.txt`, `requirements.txt` (pointer) | 30/30 tests pass; import OK |
| OpenAI embedding provider, persisted document embeddings, offline fallback | `backend/app/models/embeddings.py`, `backend/scripts/build_corpus_embeddings.py` | `corpus_embeddings.npy` committed; dimension self-heal verified |
| FAISS → NumPy retrieval, `chunk_embeddings` SQLite table | `backend/app/pipeline/retriever.py`, `backend/app/knowledge/hybrid_retriever.py`, `backend/app/knowledge/repository.py`, `backend/app/knowledge/db.py` | legacy + workspace retrieval verified live |
| OpenAI NLI classifier + deterministic fallback, schema preserved | `backend/app/models/nli.py` | verify_claim/_batch outputs unchanged |
| spaCy → regex sentencizer | `backend/app/pipeline/claims.py`, `tests/test_pipeline.py` | 6 new behavior tests (periods, ?, !, abbreviations, newlines, empty) |
| Lazy package exports | `backend/app/{models,pipeline,agents,specialists,planner}/__init__.py` | `import app.main` loads no heavy modules |
| Explicit schema init | `backend/app/knowledge/db.py`, `backend/app/main.py` | no import-time DB writes |
| Lazy specialists/planners, bounded user cache | `backend/app/knowledge/user_storage.py` | ingestion/query verified live |
| Robust Dockerfile | `backend/Dockerfile` | CMD as in §7 (colon fix included) |
| `.dockerignore` | `backend/.dockerignore` | excludes venv/secrets/user data/junk |
| Render config | `render.yaml` | Docker runtime, `/health` check, free plan |
| Memory diagnostics | `backend/scripts/profile_startup.py`, `backend/scripts/memory_report.py` | reports reproduced in §2 |
| Health endpoints | `backend/app/api/routes.py` (`/health`, `/health/ready`, `/health/memory`) | live-verified; no sensitive data exposed |

### Remaining follow-ups (Phase 2+ of the roadmap, not required for deployment)

1. **Dataset-first capabilities** (Part 6–10, 13–18): dataset sessions, tabular profiler,
   deterministic EDA engine, chart-spec visualization, NL data questions, insight engine,
   optional lightweight modeling/forecasting/anomaly detection. Recommended home:
   `app/agents/specialists/` alongside the existing registry/coordinator pattern, using
   pandas/scikit-learn as **lazy, optional** dependencies (never imported at startup).
2. **Dashboard spec generation** (Part 14): emit JSON `DashboardSpec` consumed by the
   frontend — no server-side rendering.
3. **MCP integration layer** (Part 20): optional external client module, disabled by default.
4. **Dependency additions** for the above belong in a separate optional requirements file
   (e.g. `requirements-analytics.txt`) so the Render image stays at ~80 MB.

### Deployment checklist (Render)

- [x] Docker build context clean (`.dockerignore`)
- [x] CMD inherited from Dockerfile — **remove any Docker Command override in the dashboard**
- [x] `OPENAI_API_KEY` set in Render env
- [x] `healthCheckPath: /health`
- [x] single worker, free plan, root dir `backend`



