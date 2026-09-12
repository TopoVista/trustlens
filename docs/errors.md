# TrustLens limitation and error register

## Evidence and language limits

| Risk | Why it happens | Mitigation or user-facing behavior |
|---|---|---|
| Missing support | The relevant fact is absent from the active workspace or was not retrieved. | Return unresolved or unsupported status and ask for a better source rather than inventing support. |
| Overstated claim | A generated synthesis can phrase evidence more broadly than a passage warrants. | Review atomic claims and source excerpts; improve evaluation and calibration before relying on automation. |
| Apparent contradiction | Sources can differ by date, scope, definition, draft status, or authority. | Show source context and authority. Treat a conflict as a review signal, not an automatic conclusion. |
| Weak authority signal | Authority level is declared with ingestion and is not an independent credential check. | Make authority visible and use workspace policies for context-specific treatment. |
| Provider degradation | External provider calls can fail, time out, or be unavailable. | Preserve clear fallback behavior and do not describe it as the same as provider-backed verification. |

## Operational limits

| Risk | Check | Response |
|---|---|---|
| Documents disappear after deployment event | `GET /api/me/storage` reports SQLite and `durable: false`. | Configure Render Postgres `DATABASE_URL`, redeploy, then re-ingest lost sources. |
| Vercel cannot call API | Browser Network error, CORS failure, or unexpected URL. | Verify `VITE_API_URL`, Render health, and CORS origins; rebuild Vercel after environment changes. |
| Authenticated user receives 401 or 404 | JWT settings or workspace ownership does not match. | Inspect verified token issuer/audience and the caller's workspace ownership; do not weaken ownership checks. |
| First request is slow | Render Free service has been idle. | Wait for the service to wake and retry; treat it as a deployment characteristic. |
| Confidence looks implausible | Different API contracts may use ratios or percentages. | Use `toConfidencePercent`; values are normalized and clamped in the current frontend. |

## Unsupported assumptions to avoid

- Do not call an unresolved claim false.
- Do not call an authority level a third-party certification.
- Do not say local Render SQLite persists across restart.
- Do not say the current browser uploader parses PDF, DOCX, images, or OCR input.
- Do not say confidence is a probability of truth.
- Do not claim live deployment settings based only on repository configuration.
