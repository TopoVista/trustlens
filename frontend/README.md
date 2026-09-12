# TrustLens frontend

The frontend is a React 18 and Vite single-page application for the TrustLens
evidence workspace. It does not embed a backend URL: Vite compiles
`VITE_API_URL` into each deployment.

## Commands

```powershell
cd frontend
npm install
npm run dev
npm test
npm run build
```

`npm test` exercises the confidence-formatting utility. `npm run build` creates
the Vercel-ready `dist` directory.

## Environment

Copy `.env.example` to `.env` and set:

```ini
VITE_API_URL=http://localhost:8000
```

For production, configure this value in Vercel with the deployed Render API
origin, without a trailing slash. If Clerk is enabled, provide the project's
publishable key through the existing frontend environment configuration. Never
place a backend secret or a `DATABASE_URL` in a Vite variable.

## Product composition

- `src/App.jsx` hydrates authentication, workspaces, storage state, source
  register data, health, graph, timeline, rules, ingestion, and query results.
- `src/api.js` contains all browser HTTP calls and token/header attachment.
- `src/components/KnowledgeHeader.jsx` manages the active workspace and creates
  new ones.
- `src/components/IngestionModal.jsx` collects content and authority, and shows
  the returned document ID and authority after ingestion.
- `src/components/AnswerContractPanel.jsx` renders synthesis, claims, evidence,
  conflicts, uncertainty, and a normalized confidence percentage.
- `src/components/DocumentLibrary.jsx`, `HealthAuditDashboard.jsx`,
  `KnowledgeGraphTimeline.jsx`, and `SemanticRulesManager.jsx` provide the
  persistent workspace views.

The current visual system is a deep-ink evidence desk with restrained
violet/cyan accents and the original generated image at
`src/assets/trustlens-verification-hero.png`. The image is decorative; it does
not represent a source, a score, or an evidence result.

## Important behavior

The UI preserves source provenance instead of keeping it in a temporary toast:
the document library displays document ID, declared authority, and ingestion
status after every refresh. The storage label is intentionally descriptive,
not a guarantee: use the API response from `/api/me/storage` to establish
whether the connected backend is durable Postgres or local SQLite.
