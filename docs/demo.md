# TrustLens demo walkthrough

## Before the demo

1. Confirm the API responds at `/health`.
2. Confirm Vercel was built with the intended `VITE_API_URL`.
3. If demonstrating retention, open `/api/me/storage` after authentication and confirm `storage_backend: "postgres"` and `durable: true`.
4. Start with an empty or known workspace so source counts are easy to explain.

## Suggested five minute flow

### 1. Set the expectation

Open TrustLens and explain that it is an evidence workspace, not a normal chat window. The product stores source records and makes the evidence behind an answer reviewable.

### 2. Create or select a workspace

Use the workspace picker in the header. Create a workspace such as "Product launch review" and explain that workspace routes are owner-scoped on the API.

### 3. Ingest two related sources

Open **Add documents**. Use a sample pack or paste two short sources with a deliberate difference, for example one planned launch date and one revised date. Select an authority level for each source.

After each ingestion, point out:

- the success state shows the returned document ID and authority;
- the source register retains ID, authority, and status after refresh;
- ingestion also creates chunks and may extract claims, entities, and dates.

### 4. Ask an evidence question

In the evidence desk, ask: "Are there any conflicting dates or budget numbers across documents?" Explain that the frontend sends the question to the active workspace and the planner chooses relevant specialist capabilities.

### 5. Review the answer contract

Open the **Claims** and **Evidence** tabs. Explain that a confidence percentage is a bounded grounding signal, not a guarantee of truth. If there are conflicts or gaps, show those views and use the wording "available workspace evidence" rather than making a broader factual claim.

### 6. Explore the record

Open **Evidence health** for aggregate signals, then **Knowledge map** for entities and events. Finish at **Verification rules** to show that a workspace can contain context-specific review policies.

## Honest demo language

- Say "this source is declared HIGH authority" rather than claiming independent certification of the source.
- Say "unresolved by the current workspace evidence" rather than "false."
- Say "durable Postgres is active" only if `/api/me/storage` confirms it.
- Do not promise PDF, DOCX, image, or OCR ingestion from the current browser upload experience; demonstrate supported text-based sources.
