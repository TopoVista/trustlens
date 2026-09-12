# TrustLens

TrustLens is an evidence-first workspace for working with your own documents.
It ingests text-based source material into a private workspace, extracts claims,
entities, and time anchors, then lets a user ask questions with the supporting
record kept visible. The product is designed around one principle: a generated
answer is not proof; the evidence behind it must remain reviewable.

## Current product capabilities

- Private, owner-scoped workspaces with Clerk-aware browser authentication.
- Direct-text and supported text-file ingestion with a returned document ID,
  declared authority level, ingestion status, and semantic chunk count.
- Evidence-grounded workspace queries with an answer contract for synthesis,
  atomic claims, retrieved evidence, contradictions, and unresolved items.
- Evidence health metrics, proactive discovery signals, an entity map, a
  chronological timeline, and workspace-specific verification policies.
- A React/Vite frontend with an original TrustLens verification visual and an
  evidence-centered review interface.
- Local SQLite storage for development and durable Postgres storage when
  `DATABASE_URL` is configured.

## Architecture

```text
Browser (React / Vite / Clerk)
        |
        | VITE_API_URL, bearer token when configured
        v
FastAPI routes and authorization
        |
        +--> Workspace repository --> SQLite locally or Postgres with DATABASE_URL
        |
        +--> Ingestion: documents -> chunks -> claims/entities/events/evidence links
        |
        +--> Planner -> relevant in-process specialist capabilities -> answer contract
        |
        +--> Optional OpenAI providers for generation, embeddings, and verification
```

The production service does not rely on local PyTorch, Transformers, FAISS,
spaCy, or sentence-transformer runtime dependencies. OpenAI-backed providers
are loaded only when needed, and deterministic fallback behavior supports
degraded operation when a provider is unavailable.

## Local development

Prerequisites: Python 3.11+ (3.12/3.13 also work), Node.js 18+, and optionally
an OpenAI API key for provider-backed analysis.

```powershell
# Backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

```powershell
# Frontend, in another terminal
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Set `VITE_API_URL=http://localhost:8000` in `frontend/.env`. For local
development, configure backend authentication as described in
[backend/README.md](backend/README.md).

## Production deployment

`render.yaml` defines a Docker Render web service and a `trustlens-postgres`
database for Blueprint deployments. Vercel should deploy the `frontend`
directory with `VITE_API_URL` set to the deployed Render API URL.

Important: a manually created Render web service does not become durable merely
because this repository contains a Blueprint. Create or connect a Render
Postgres database, set its internal connection string as `DATABASE_URL`, and
redeploy. The live source of truth is `GET /api/me/storage`: durable Postgres
reports `storage_backend: "postgres"` and `durable: true`. SQLite on a Render
free web service is ephemeral.

Never commit `OPENAI_API_KEY`, JWT keys, a `DATABASE_URL`, or a frontend
environment file containing real secrets.

## Verification and tests

```powershell
# From the repository root
pytest tests -q

# From frontend
npm test
npm run build
```

The frontend confidence helper accepts both a 0-1 ratio and an already scaled
0-100 percentage, then clamps the rendered value to 0-100. This prevents a
valid value such as `94.1` from being displayed as `9410%`.

## Documentation

- [Project architecture](docs/architecture.md)
- [Implementation status](docs/IMPLEMENTATION_STATUS.md)
- [Render deployment review](docs/RENDER_FREE_AUDIT.md)
- [Render persistence setup](docs/RENDER_PERSISTENCE_SETUP.md)
- [Dataset analytics API](docs/DATASET_ANALYTICS.md)
- [Demo walkthrough](docs/demo.md)
- [Evaluation plan](docs/evaluation.md)
- [Error and limitation register](docs/errors.md)
- [Ablation plan](docs/ablation.md)
- [Historical baseline-output note](docs/baseline_outputs.md)
- [Workflow and interview guide](docs/TrustLens_Project_Workflow_and_Interview_Guide.docx)
- [Top-ten code guide](docs/TrustLens_Top_Ten_Important_Files_Code_Guide.docx)

## Scope and limits

TrustLens is a document evidence-review tool, not a certification of objective
truth. `NOT_SUPPORTED` or `UNRESOLVED` means the available workspace evidence
does not establish a claim; it does not mean the claim is objectively false.
Review source passages for decisions with legal, financial, medical, security,
or other high-stakes consequences.
