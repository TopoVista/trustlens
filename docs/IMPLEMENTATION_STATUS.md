# TrustLens implementation status

## Completed product path

The active product path is implemented and connected end to end:

- Workspace list and creation are owner-scoped.
- Text-based source ingestion creates a document record, chunks, and enrichment data.
- The ingestion response includes document ID, authority level, chunk count, and status; the frontend also retains this information in the source register after refresh.
- Workspace queries return a synthesis contract with claims, evidence, contradictions, unknowns, plan trace, intent, and latency when available.
- Source register, evidence health, discovery signals, knowledge map, timeline, and verification rules have dedicated frontend views.
- Frontend confidence formatting accepts a ratio or percentage contract and safely clamps display to `0-100%`.
- Production auth verifies Bearer JWTs and enforces workspace ownership. Development mode remains available for local iteration only.
- Durable persistence is supported through Postgres whenever the running service has `DATABASE_URL`.
- Render Blueprint configuration declares the Docker service, CORS policy, production auth mode, and `trustlens-postgres` database binding.

## Current deployment conditions

The repository is ready to declare durable storage, but a manually created Render
service must still have a real Postgres connection added in the dashboard. The
presence of `render.yaml` does not alter an existing service automatically.

Use `GET /api/me/storage` to establish the active mode:

| Response field | Durable production value | Meaning |
|---|---|---|
| `storage_backend` | `postgres` | Repository is using the managed database connection. |
| `durable` | `true` | Workspace documents survive web-service restarts and redeploys, subject to the database plan lifecycle. |
| `storage_backend` | `sqlite` | Local storage mode is active. On Render Free, this is ephemeral. |
| `durable` | `false` | Do not promise persistence across restart or redeploy. |

## Current frontend state

The current client has been refactored around a single evidence-desk visual
system. It preserves the previous product flows while making source provenance
and review state clearer:

- A private-workspace hero explains the intended use without presenting a decorative image as evidence.
- The source register displays ID, authority, and ingestion status for every document.
- The answer panel offers synthesis, claims, evidence, and conflict views.
- The ingestion success state shows the exact returned document ID and authority.
- The architecture modal describes the current OpenAI-backed, lazy provider path instead of removed local model tooling.

## Known limits and honest boundaries

- The browser upload tab currently reads supported text-based files (`.txt`, `.md`, `.csv`, `.json`) before sending their text. It is not a promise of server-side PDF, DOCX, or image OCR support.
- External AI provider availability can affect generation, embeddings, or verification enrichment. Fallback behavior is intentionally conservative and should not be represented as equivalent to full provider-backed analysis.
- A confidence value is an evidence-grounding signal, not a probability of objective truth.
- Render Free services can spin down. A first request can be slower while the service wakes.
- Render Free Postgres has a plan lifecycle; review Render's current plan rules before treating it as permanent production retention.

## Verification commands

```powershell
pytest tests -q

cd frontend
npm test
npm run build
```

## Documentation maintenance rule

When changing deployment, auth, persistence, or the public API, update this
file, `README.md`, `docs/architecture.md`, and the corresponding deployment or
frontend guide in the same change. Do not keep historical phase plans framed as
the current implementation.
