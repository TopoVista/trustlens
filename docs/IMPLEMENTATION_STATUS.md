# TrustLens Implementation Status

## Current State

### Branch
- `main` — Phase 0 audit + Phase 2 (Data Analytics) + Security Hardening (JWT auth + workspace ownership) complete

### Architecture
- FastAPI backend (single process, single uvicorn worker) on Render Free
- Per-user SQLite databases under `data/users/{user}/trustlens_knowledge.db`
- OpenAI SDK for LLM generation/verification (NO local ML models)
- NumPy-only lightweight analytics engine (`app/analytics/`)
- Dataset endpoints: `/datasets/upload`, `/profile`, `/eda`, `/insights`, `/charts`, `/list`, `/{id}`, `DELETE /{id}`
- Legacy RAG: `/answer`, `/analyze`, `/api/assess`, `/api/ask`
- Personal knowledge: `/api/workspaces/*`, `/api/me`
- Frontend: React/Vite, Clerk auth, sends `x-user-id`

### Authentication & Authorization (P0 — FIXED)
- JWT signature verification (`PyJWT[cryptography]`): signature, `exp` (required), `iat`, `nbf`, issuer, audience, algorithm — all validated via `ALLOWED_ALGORITHMS`
- **`none` algorithm explicitly rejected** (not in allowed list)
- `AUTH_MODE=prod` (Render default per `render.yaml`): Bearer JWT required; user ID comes from the verified `sub` claim
- `AUTH_MODE=dev` (local only): `x-user-id` header accepted and marked `is_authenticated=False`
- **Workspace ownership enforced on every workspace-scoped route** (`enforce_workspace_ownership`): IDOR/cross-user access returns 404 (no existence leakage)
- `workspaces.owner_user_id` column added via safe `ALTER TABLE` migration (existing DBs preserved)
- `create_workspace`/`list_workspaces`/`ensure_default_workspace` all owner-scoped
- New `/api/me` field: `auth_method` (additive, backward-compatible)

### Memory
- Idle RSS: ~80 MB (target < 120 MB) ✓
- Request RSS: ~80–120 MB (target < 180 MB) ✓
- No heavy modules at startup ✓

### Tests
- 86 tests pass (70 prior + 16 new security tests)

### P0/P1/P2 Issues
#### Fixed in this phase
1. ~~Unverified JWT~~ — signature/claims verified in `app/api/auth.py`; forged/expired/`none`-alg tokens rejected (16 tests)
2. ~~X-User-Id trust~~ — production requires a verified Bearer JWT; dev mode explicitly marked
3. ~~No workspace ownership~~ — every workspace route enforces `owner_user_id`
9. ~~File upload = raw text~~ — dataset upload supports raw + multipart
#### Remaining (Phase 3+)
4. Eager registry — `AgentRegistry.__init__` constructs all 15 specialists
5. Eager ingestion sub-agents — `IngestionKnowledgeAgent.__init__` creates 4 sub-agents
6. EvidenceAgent fake evidence — falls back to `chunks_data[0]`
7. No ingestion transaction/state — no PENDING/PROCESSING/READY/FAILED
8. No content-hash dedup
10. Numeric parsing wrong — strips all $/% blindly, no percentage handling
11. Categorical top_values uses `list(set())` — not actual top-freq
12. Correlation only first 2 numeric columns — not all pairs
13. Quartiles via index — not true percentile
14. Verifier error → neutral — wrong semantics
15. Planner over-executes — runs entity/claim/evidence always
