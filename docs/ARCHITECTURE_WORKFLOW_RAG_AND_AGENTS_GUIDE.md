# TrustLens Architecture, Workflow, RAG, and Specialist Guide

> **Source-grounded guide.** This document describes the implementation in this repository as of commit `683b2be`. Code excerpts are shortened only for readability; links point to the authoritative implementation. A term such as “agent” means an in-process Python specialist class unless this document explicitly says otherwise. It does **not** mean an autonomous background service, a separately deployed model, or a human reviewer.

## 1. What TrustLens is

TrustLens is an evidence-review application for a user's own documents. A user creates an isolated workspace, ingests text or tabular content, and asks a question. The system retrieves relevant source passages, applies only the specialists relevant to the question, and returns an answer contract that keeps claims, source passages, contradictions, and unknowns reviewable.

The central product promise is deliberately narrower than “truth detection”:

- It can report whether the **available workspace record** supports, contradicts, or fails to establish a statement.
- It cannot establish whether a source document is authentic, complete, current, or objectively true outside the workspace.
- An answer is an analysis of uploaded evidence, not a legal, medical, financial, compliance, or security certification.

## 2. Architecture at a glance

```text
                         ┌────────────────────────────────────┐
                         │ Browser: React + Vite              │
                         │ pages: Query / Documents / Health  │
                         │ Map / Rules                        │
                         └───────────────┬────────────────────┘
                                         │ HTTPS + bearer token when enabled
                                         │ POST SSE for live query stages
                                         ▼
                         ┌────────────────────────────────────┐
                         │ FastAPI                             │
                         │ auth → ownership check → route      │
                         └───────┬───────────────────────┬─────┘
                                 │                       │
                 document route │                       │ workspace query route
                                 ▼                       ▼
             ┌────────────────────────┐    ┌───────────────────────────┐
             │ Ingestion specialist   │    │ AnalysisPlanner           │
             │ chunks / entities /    │    │ intent → retrieval →      │
             │ claims / events        │    │ selected specialists →    │
             └───────────┬────────────┘    │ synthesis answer contract  │
                         │                 └───────────┬───────────────┘
                         ▼                             ▼
             ┌──────────────────────────────────────────────────────────┐
             │ KnowledgeRepository                                      │
             │ workspaces, documents, chunks, embeddings, claims,       │
             │ evidence, entities, events, rules, profiles              │
             └─────────────────────┬────────────────────────────────────┘
                                   │ SQLite locally / Postgres with DATABASE_URL
                                   ▼
             ┌──────────────────────────────────────────────────────────┐
             │ Optional provider boundary                                │
             │ OpenAI embeddings, NLI classification, grounded synthesis │
             │ deterministic fallbacks when unavailable                  │
             └──────────────────────────────────────────────────────────┘
```

### Main implementation areas

| Area | Main files | Responsibility |
| --- | --- | --- |
| Browser application | [frontend/src/App.jsx](../frontend/src/App.jsx), [frontend/src/api.js](../frontend/src/api.js) | Loads workspace data, owns the browser route/view state, calls APIs, reads SSE, and renders the answer contract. |
| HTTP and authorization boundary | [backend/app/main.py](../backend/app/main.py), [backend/app/api/routes.py](../backend/app/api/routes.py), [backend/app/api/auth.py](../backend/app/api/auth.py) | Starts FastAPI, configures CORS, authenticates requests, and checks workspace ownership before data access. |
| Persistence | [backend/app/knowledge/db.py](../backend/app/knowledge/db.py), [backend/app/knowledge/repository.py](../backend/app/knowledge/repository.py) | Portable SQLite/Postgres access and the workspace-scoped record model. |
| Ingestion | [backend/app/specialists/ingestion_agent.py](../backend/app/specialists/ingestion_agent.py) | Deduplicates and persists a document, chunks it, then extracts claims, entities, events, and optional table statistics. |
| Workspace RAG | [backend/app/knowledge/hybrid_retriever.py](../backend/app/knowledge/hybrid_retriever.py), [backend/app/models/embeddings.py](../backend/app/models/embeddings.py) | Creates/persists chunk vectors, embeds one query, ranks workspace-local passages. |
| Intent-aware verification | [backend/app/planner/planner.py](../backend/app/planner/planner.py), [backend/app/planner/registry.py](../backend/app/planner/registry.py) | Classifies the question, invokes the smallest useful specialist set, and returns a structured answer contract. |
| Claim verification | [backend/app/specialists/evidence_agent.py](../backend/app/specialists/evidence_agent.py), [backend/app/models/nli.py](../backend/app/models/nli.py) | Evaluates claim–passage pairs as entailment, contradiction, or neutral. |

## 3. Product analysis path: workspace evidence intelligence

The current frontend uses workspace endpoints under `/api/workspaces/{workspace_id}/...`. Its normal query path is:

```text
Upload source → persistent workspace records → hybrid retrieval
→ intent-aware specialist dispatch → evidence-grounded synthesis
→ answer / claims / evidence / contradictions / unknowns
```

This is the path used by the Documents, Verify, Evidence Health, Knowledge Map, and Verification Rules views.

## 4. End-to-end user workflow

### 4.1 Startup and identity

1. The React application starts from [frontend/src/main.jsx](../frontend/src/main.jsx) and composes the application in `App.jsx`.
2. If Clerk is configured, the browser obtains a token and the API client sends it as a Bearer token. Without Clerk, the local/development authentication mode is used.
3. `GET /api/workspaces` calls `ensure_default_workspace`, so an authenticated user with no workspace receives one.
4. Every workspace route calls `enforce_workspace_ownership(...)` before reading or writing workspace records.

The important architectural point is that a workspace identifier by itself is not authorization. The route validates the caller, then the repository verifies that `owner_user_id` matches the caller.

```python
# backend/app/api/routes.py — representative workspace boundary
@router.get("/api/workspaces/{workspace_id}/documents")
def get_workspace_documents(workspace_id, user=Depends(get_current_user),
                            ctx=Depends(get_current_user_context)):
    enforce_workspace_ownership(user, workspace_id, ctx.repo)
    return ctx.repo.get_documents(workspace_id)
```

### 4.2 Document ingestion

The frontend sends title, filename, raw text, file type, and declared authority to:

```text
POST /api/workspaces/{workspace_id}/documents
```

The route owns no extraction logic. It performs authorization and delegates to `IngestionKnowledgeAgent.ingest_content`:

```python
# backend/app/api/routes.py
enforce_workspace_ownership(user, workspace_id, ctx.repo)
return await ctx.ingestion_agent.ingest_content(
    workspace_id=workspace_id,
    title=request.title,
    filename=request.filename or "document.txt",
    raw_content=request.raw_content,
    file_type=request.file_type or "text",
    authority_level=request.authority_level or "MEDIUM",
)
```

The ingestion lifecycle is intentionally observable:

```text
SHA-256 dedupe check
  → document row: PROCESSING
  → optional CSV/TSV profile
  → structural chunks
  → entities
  → claims + ingestion-time evidence links
  → timeline events
  → document row: READY
  → return ID, authority, counts, status
```

If an exception occurs after the document is created, status becomes `FAILED` and a shortened error is recorded. If the exact same raw content hash has already been ingested in the same workspace, the existing ingestion summary is returned rather than duplicating the document.

```python
# backend/app/specialists/ingestion_agent.py — lifecycle shape
content_hash = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()
existing = self.repo.find_document_by_hash(workspace_id, content_hash)
if existing:
    return self.repo.get_document_ingestion_summary(workspace_id, existing["id"])

doc_id = self.repo.add_document(..., ingestion_status="PROCESSING")
try:
    chunks_data = self._chunk_document(workspace_id, doc_id, raw_content, is_tabular)
    self.repo.add_chunks(chunks_data)
    # entity, claim, evidence, and event extraction follows
    self.repo.update_document_ingestion_status(workspace_id, doc_id, "READY")
except Exception as exc:
    self.repo.update_document_ingestion_status(workspace_id, doc_id, "FAILED", str(exc)[:500])
    raise
```

### 4.3 What is persisted

The core relational model is:

```text
workspace (owner) ──< documents ──< chunks ──< chunk_embeddings
      │                  │              │
      │                  ├──< claims ───┴──< evidence
      │                  └──< events
      ├──< entities ──< relationships
      ├──< semantic_rules
      └──< dataset_profiles
```

Key design choices:

- All operational records carry `workspace_id`; repository reads filter on it.
- `documents` retain raw content, declared `authority_level`, hash, status, and error state.
- `chunks` keep a source coordinate such as `Section 2, Paragraph 1` or a row range.
- `evidence` is first-class: it can hold `SUPPORTS`, `CONTRADICTS`, or `QUALIFIES`, plus exact passage, location, and strength.
- Chunk embeddings are binary `float32` vectors in the database, preventing re-embedding every document for every question.
- SQLite is the local default; a configured `DATABASE_URL` switches to Postgres. Render persistence is durable only in the latter configuration.

## 5. Chunking and claim splitting

These are related but different operations. A good interview response calls out that distinction.

### 5.1 Document chunks are retrieval units

For ordinary text, ingestion splits on blank-line paragraph boundaries, discards very short paragraphs, and records a section/paragraph location. It does **not** currently use token-window chunking, overlap, PDF page extraction, or semantic boundary models.

```python
# backend/app/specialists/ingestion_agent.py
paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if len(p.strip()) > 30]
if not paragraphs:
    paragraphs = [content.strip()]

for idx, paragraph in enumerate(paragraphs):
    chunks.append({
        "workspace_id": workspace_id,
        "document_id": doc_id,
        "chunk_index": idx,
        "text": paragraph,
        "location_info": f"Section {idx + 1}, Paragraph 1",
    })
```

For text identified as CSV or TSV, the chunker repeats the header and groups rows in batches of 15. This keeps a table context available to retrieval while preserving useful row-range provenance.

### 5.2 Claims are assertion units

A claim is a sentence-level factual assertion that can be independently reviewed. The code uses a conservative deterministic sentencizer in [backend/app/pipeline/claims.py](../backend/app/pipeline/claims.py), rather than an LLM or spaCy model.

Algorithm:

1. Split input by non-empty line.
2. Remove leading Markdown list markers such as `-`, `*`, and `1.`.
3. Temporarily replace periods in a fixed abbreviation list (`e.g.`, `Dr.`, `U.S.`, months, and so on).
4. Split remaining text only at `.`, `!`, or `?` followed by whitespace.
5. Restore abbreviations.
6. Discard fragments shorter than five characters.
7. Normalize whitespace and preserve modal language such as *may*, *can*, and *might*.

```python
# backend/app/pipeline/claims.py
protected = _protect_abbreviations(text.strip())
parts = re.split(r"(?<=[.!?])\s+", protected)

for line in text.splitlines():
    line = re.sub(r"^(\d+\.|\*|-)\s+", "", line.strip())
    for sentence in _split_sentences(line):
        if len(sentence.strip()) >= _MIN_CLAIM_LEN:
            claims.append(sentence.strip())
```

Why protect abbreviations? Without it, `The U.S. team reported 3.5%.` could become incorrect fragments. Why preserve hedges? Changing “may reduce risk” to “reduces risk” would make the verification target stronger than the source actually says.

### 5.3 Claim Detective: extraction, de-duplication, typing

`ClaimDetective` uses the splitter above and adds project-specific policy:

- It ignores statements shorter than 15 characters.
- It normalizes for comparison, then de-duplicates case-insensitively within one analysis context.
- It labels a statement `METRIC` if it contains a digit or a currency/percentage symbol; otherwise it uses `FACTUAL`.
- Its initial `0.85` / `0.75` confidence is a heuristic extraction confidence, **not** evidence verification confidence.

```python
# backend/app/specialists/claim_detective.py
for statement in split_into_claims(text):
    if len(statement.strip()) < 15:
        continue
    normalized = normalize_claim(statement)
    if normalized.lower() in seen:
        continue
    claim_type = "METRIC" if any(ch.isdigit() or ch in "$%€" for ch in statement) else "FACTUAL"
    claims.append({"statement": statement, "normalized_statement": normalized,
                   "claim_type": claim_type, "status": "UNRESOLVED"})
```

### 5.4 Ingestion-time claims versus query-time claims

TrustLens has two claim moments:

| Moment | Input | Goal | Storage effect |
| --- | --- | --- | --- |
| Ingestion | Entire uploaded document | Populate the workspace claim/evidence record | Creates `claims`; links a chunk only when lexical overlap is at least 0.70 or the exact statement occurs. |
| Query | The *retrieved passages* for one question | Analyze the evidence relevant to the question now | Creates an in-memory result for the answer contract; it does not write a second copy to the claim graph. |

The ingestion matcher is deliberately conservative. It only links a chunk when the exact assertion is contained in it or when lexical overlap clears the threshold; it does not attach a random first paragraph merely to make every claim look cited.

```python
# backend/app/specialists/ingestion_agent.py
if statement.lower() in text.lower():
    return chunk
score = len(claim_tokens & chunk_tokens) / len(claim_tokens)
return best if score >= 0.7 else None
```

## 6. How current workspace RAG works

RAG means **retrieval-augmented generation**: retrieve relevant context first, then constrain synthesis to that context. In TrustLens, retrieval also feeds claim verification and specialist tools; it is more than just “put top passages in a prompt.”

### 6.1 Indexing / embedding time

At ingestion, chunk text is persisted immediately. The first retrieval needing a chunk vector computes missing vectors and saves them to `chunk_embeddings`. Later requests reuse that vector. Embeddings come from OpenAI (`text-embedding-3-small` by default) when configured; otherwise deterministic feature hashing produces a 512-dimensional normalized vector so the application degrades rather than crashes.

```python
# backend/app/knowledge/hybrid_retriever.py
stored = self.repo.get_chunk_embeddings(workspace_id)
pending = [chunk for chunk in chunks if chunk["id"] not in stored]
if pending:
    vectors = model.encode([p["text"] for p in pending], normalize_embeddings=True)
    for chunk, vector in zip(pending, vectors):
        self.repo.set_chunk_embedding(workspace_id, chunk["id"],
                                      vector.astype(np.float32).tobytes(),
                                      len(vector), model.get_model_name())
```

Important implementation nuance: a vector dimension mismatch, such as an older offline vector after later OpenAI availability, causes stale vectors to be re-embedded or fitted to the expected dimension. This avoids a matrix-shape crash. The fallback is operationally useful but semantically weaker than model embeddings.

### 6.2 Query-time retrieval and ranking

For one workspace question:

1. Read only chunks whose `workspace_id` matches the requested workspace.
2. Embed the query once. Single-text embeddings are memoized in a bounded in-memory cache.
3. Form an embedding matrix from persisted vectors in chunk order.
4. Calculate cosine similarity as a dot product because both query and chunk vectors are normalized.
5. Add a small lexical boost for query words longer than three characters that occur in a chunk.
6. Weight by the user-declared source authority: `HIGH × 1.15`, `MEDIUM × 1.0`, `LOW × 0.85`.
7. Sort descending and return the top `k` passages (the planner uses `k=6`).

Mathematically, for a chunk `c` and normalized query `q`:

```text
semantic(c, q) = c · q                         # cosine similarity
keyword(c, q) = min(0.15, 0.03 × overlap_count)
raw(c, q) = semantic(c, q) + keyword(c, q)
rank(c, q) = raw(c, q) × authority_multiplier(c)
```

```python
# backend/app/knowledge/hybrid_retriever.py
sim_scores = np.dot(chunk_embs, query_emb)
overlap = sum(1 for term in query_terms if len(term) > 3 and term in chunk_lower)
final_score = float(sim_scores[idx]) + min(0.15, overlap * 0.03)
if authority == "HIGH":
    final_score *= 1.15
elif authority == "LOW":
    final_score *= 0.85
```

The class is called `HybridKnowledgeRetriever` because it combines dense semantic similarity, lexical overlap, authority weighting, and can expose entity context. In the present `retrieve(...)` implementation, the primary ranked output is dense-plus-keyword-plus-authority; graph traversal is not blended into that final score.

### 6.3 Grounded generation and verification are separate

The Synthesis Specialist receives retrieved passages plus specialist findings and uses a low-temperature OpenAI completion when available. Its prompt says to answer strictly from workspace evidence, distinguish fact from inference, name insufficient evidence, and not hide contradictions.

After retrieval, the Evidence Specialist independently tests candidate claims against candidate passages. This separate check is crucial: source-grounded generation reduces hallucination pressure, while NLI-style verification tests whether each output assertion is actually entailed, contradicted, or left neutral by its evidence.

### 6.4 Fallbacks and their meaning

| Capability | Preferred path | Fallback | Honest interpretation |
| --- | --- | --- | --- |
| Embeddings | OpenAI embedding API | Normalized hashed unigram/bigram features | Retrieval stays available, but semantic recall is weaker. |
| NLI | OpenAI JSON classification | Token overlap + negation + numeric-conflict heuristics | A continuity heuristic, not equivalent to semantic NLI. |
| Synthesis | OpenAI grounded completion | First retrieved passage or insufficiency statement | A source excerpt, not a natural-language reasoning replacement. |

## 7. Intent planning and selective dispatch

The [AnalysisPlanner](../backend/app/planner/planner.py) is the controller of the current workspace query path. It does not run every specialist for every request.

### 7.1 Intent classifier

The implementation is deterministic keyword/rule classification:

| Intent | Examples of routing signals | Additional specialists |
| --- | --- | --- |
| `FACTUAL_QUERY` | Default | entities, claims, evidence, synthesis |
| `WHY_ANALYSIS` | `why`, `reason`, `cause` | entities, claims, evidence, contradiction, timeline, gap, synthesis |
| `CONTRADICTION_QUERY` | `contradict`, `conflict`, `disagree`, `differ` | claims, evidence, contradiction, synthesis |
| `GAP_QUERY` | `missing`, `gap`, `blind spot`, `unknown` | claims, evidence, gap, synthesis |
| `COMPARISON_QUERY` | `compare`, `difference between`, `versus`, `vs` | entities, comparison, synthesis; skips claim/evidence pass |
| `DISCOVERY_QUERY` | `pattern`, `trend`, `anomaly`, `what should I know` | entities, claims, evidence, pattern hunter, synthesis |

```python
# backend/app/planner/planner.py
if "compare" in q or "difference between" in q or "versus" in q or " vs " in q:
    return "COMPARISON_QUERY"
elif "pattern" in q or "trend" in q or "anomaly" in q:
    return "DISCOVERY_QUERY"
return "FACTUAL_QUERY"
```

This is transparent and low latency, but it is not semantic intent classification. A question whose wording does not contain the defined cues can fall into `FACTUAL_QUERY`. That is a known product/design tradeoff, not an LLM planning claim.

### 7.2 Execution order

```text
classify intent
  → retrieve up to 6 workspace passages
  → contextual entity extraction for applicable intents
  → claim extraction + evidence verification except comparison
  → intent-specific specialist(s)
  → synthesis
  → package answer contract
```

For comparison, the planner intentionally compares the two highest-ranked passages instead of manufacturing a claim-verification pipeline first. The regression test in [tests/test_planner_dispatch.py](../tests/test_planner_dispatch.py) verifies that `claim_detective` and `evidence_agent` do not run on a comparison query.

## 8. Current workspace specialists: what each one does

### 8.1 Ingestion Specialist

**When it runs:** document upload only.  
**Input:** raw content, title, filename, type, authority.  
**Output:** durable records plus counts/status.

It orchestrates the ingestion sequence described earlier. It creates no external job queue; the ingestion work is awaited inside the request. CSV/TSV-like input triggers `DataAnalyst` profiling before chunks are stored.

### 8.2 Claim Detective

**When it runs:** document ingestion and most queries except comparison.  
**Method:** deterministic sentence splitting, normalization, local dedupe, simple metric detection.  
**Output:** atomic statements with `FACTUAL`/`METRIC`, `UNRESOLVED`, and heuristic extraction confidence.

It is a claim extractor, not a truth evaluator. Evidence verification happens later.

### 8.3 Evidence Specialist

**When it runs:** normal factual, why, gap, contradiction, and discovery queries.  
**Method:** tests every extracted claim against every retrieved non-empty chunk using batch NLI.  
**Output:** a verified claim with direct evidence objects and one status.

Decision logic:

```text
contradiction score ≥ 0.70             → CONTRADICTED
else best entailment score ≥ 0.70       → SUPPORTED
else best entailment score ≥ 0.40       → PARTIALLY_SUPPORTED
else                                    → UNSUPPORTED (confidence 0.30)
```

```python
# backend/app/specialists/evidence_agent.py
if contradiction_found:
    status, final_confidence = "CONTRADICTED", contra_score
elif best_support_score >= 0.70:
    status, final_confidence = "SUPPORTED", best_support_score
elif best_support_score >= 0.40:
    status, final_confidence = "PARTIALLY_SUPPORTED", best_support_score
else:
    status, final_confidence = "UNSUPPORTED", 0.3
```

The evidence item carries document/chunk ID, title, original passage, location, strength, and relationship type. In an OpenAI outage, `verify_claim_batch` never raises; it evaluates with the deterministic fallback described in Section 6.4.

### 8.4 Entity Specialist

**When it runs:** ingestion and factual/why/discovery/comparison query context.  
**Method:** regex-based organizations, a fixed metric/concept vocabulary, optional user alias/term rules, deduplication, and adjacent co-occurrence relationships.  
**Output:** named entity objects and inferred `related_to` relationships.

```python
# backend/app/specialists/entity_agent.py
canonical_map[rule.get("rule_key", "").lower()] = rule.get("rule_value")
canonical_name = canonical_map.get(ent["name"].lower(), ent["name"])
```

Important limitation: ingestion persists entities with `add_entity`, but the current ingestion method does not persist the Entity Specialist's inferred relationship list. The graph endpoint therefore reflects stored entity/relationship records, and relationship persistence would need explicit `add_relationship(...)` calls to populate inferred edges.

### 8.5 Timeline Specialist

**When it runs:** ingestion and `WHY_ANALYSIS`.  
**Method:** regexes for `YYYY`, `YYYY-MM-DD`, and month-year formats; sentence-level association; approximate numeric year sort.  
**Output:** event title, date string, description, document ID, and timestamp value.

```python
# backend/app/specialists/timeline_agent.py
matches = re.findall(date_pattern, sentence)
if matches:
    year = re.search(r"\b(19\d\d|20\d\d)\b", date_str)
    events.append({"date_str": date_str,
                   "timestamp_val": float(year.group(1)) if year else 2024.0,
                   "description": sentence.strip()})
events.sort(key=lambda event: event["timestamp_val"])
```

It extracts explicit temporal references; it does not infer an unstated date or resolve all date ambiguity.

### 8.6 Contradiction Specialist

**When it runs:** why and contradiction queries.  
**Method:** pairwise review of query-time claims from different documents; checks temporal numeric differences, opposite-polarity vocabulary, and divergent values with topic overlap.  
**Output:** possible conflict records with cause (`TEMPORAL_VARIANCE`, `OPPOSITE_CONCLUSIONS`, or `METRIC_DIVERGENCE`), explanation, and severity.

This specialist is heuristic conflict detection, not a full logical consistency engine. For example, different metrics in different years are called out as low-severity temporal variance rather than silently reported as a direct factual disagreement.

### 8.7 Knowledge Gap Specialist

**When it runs:** gap and why queries.  
**Method:** converts unsupported/unresolved claims, unresolved contradictions, and missing years in a short timeline span into actionable gap records.  
**Output:** type, title, description, impact, and recommendation.

```python
# backend/app/specialists/gap_agent.py
if claim.get("status") in {"UNSUPPORTED", "UNRESOLVED"}:
    gaps.append({"type": "UNSUPPORTED_CLAIM",
                 "recommendation": "Upload primary source documentation or attestation."})
```

“Gap” means missing or unresolved **in the workspace**. It does not prove the information is absent in the world.

### 8.8 Document Comparison Specialist

**When it runs:** comparison queries when at least two passages were retrieved.  
**Method:** compares the first two ranked passages, looks for different numbers with at least three overlapping non-stopword terms, and detects newly introduced requirement language (`mandatory`, `required`, `prohibited`, `strict`, `enforced`).  
**Output:** what changed, why it matters, evidence quotes, and possible impact.

It is a substantive heuristic comparison, not a full diff across the complete pair of source files. Ranking determines which two passages are compared.

### 8.9 Pattern Hunter

**When it runs:** discovery queries.  
**Method:** counts lower-case words of five or more letters after a short stopword list; reports a term when it appears at least three times across at least two document titles; separately detects clusters of percentage/increase statements.  
**Output:** recurring theme or growth-metric cluster with evidence snippets.

The `0.88` and `0.82` values in this specialist are fixed heuristic confidence values. They are not calibrated probabilities.

### 8.10 Data Analyst

**When it runs:** ingestion when input looks tabular.  
**Method:** built-in `csv` parsing, numeric detection if at least 80% of non-null values parse numerically, descriptive statistics, IQR outlier counts, and Pearson correlation for the first two usable numeric columns.  
**Output:** row/column counts, per-column profile, insights, correlation, and data-quality metadata.

```python
# backend/app/specialists/data_analyst.py
is_numeric = len(numeric_vals) >= (len(values) * 0.8) and len(numeric_vals) > 0
q1, q3 = sorted_vals[len(sorted_vals) // 4], sorted_vals[(len(sorted_vals) * 3) // 4]
lower_bound, upper_bound = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
outliers = [value for value in numeric_vals if value < lower_bound or value > upper_bound]
```

Correlation is descriptive association, not causation. The output must never be presented as causal proof.

### 8.11 Synthesis Specialist

**When it runs:** every successful workspace query, last.  
**Method:** supplies the question, retrieved passages, semantic rules, and selected specialist findings to a constrained low-temperature prompt; uses a deterministic top-passage/insufficiency fallback.  
**Output:** the Phase 11 answer contract.

```python
# backend/app/specialists/synthesis_agent.py
return {
    "answer": answer_text,
    "confidence": confidence_pct,
    "claims": verified_claims,
    "evidence": [...retrieved_chunks...],
    "contradictions": contradictions,
    "assumptions": [...],
    "unknowns": [...knowledge_gaps...],
    "related_knowledge": {"entities": ..., "events": ...},
}
```

The currently implemented overall confidence is simple coverage: `SUPPORTED claim count / verified claim count × 100`; if no claims are verified, it is `75.0` with retrieved evidence or `20.0` without any retrieved evidence. It is not a calibrated probability of truth.

## 9. Server-Sent Events: live pipeline line

The browser issues a POST request to:

```text
POST /api/workspaces/{workspace_id}/query/stream
Content-Type: application/json
Accept: text/event-stream
```

`AnalysisPlanner.execute_plan` accepts an `on_progress` callback. As each actual stage is reached/completed, it sends an English status line such as “Searching the workspace for relevant source passages.” The API uses an async queue to serialize status events and the final result.

```python
# backend/app/api/routes.py
async def report(message: str):
    updates.put_nowait(("status", {"message": message}))
    await asyncio.sleep(0)  # yield so the response can flush

result = await ctx.planner.execute_plan(workspace_id, request.query, on_progress=report)
await updates.put(("result", result))
```

Wire shape:

```text
event: status
data: {"message":"Searching the workspace for relevant source passages."}

event: status
data: {"message":"Checking 4 atomic assertion(s) against retrieved evidence."}

event: result
data: {"query":"...","answer":"...","claims":[...], ...}
```

The frontend's `queryKnowledgeStream` parser reads `ReadableStream` chunks, buffers partial lines, parses `event:`/`data:`, shows the latest status line, and resolves only when it sees `result`. If a deployed API has not yet implemented the stream endpoint and returns `404`, the client falls back to the non-streaming query endpoint.

The stream is truthful stage reporting, not a timer-driven fake progress bar. It is still a single request: no durable task queue, resumable job, or per-stage result payload currently exists.

## 10. Confidence, support, and contradiction

Several numbers exist in the UI and backend. They have different meanings.

| Number | Produced by | Meaning | Do not call it |
| --- | --- | --- | --- |
| Extraction confidence (`0.75`/`0.85`) | Claim Detective | Heuristic confidence that a sentence is an extractable claim type | Evidence proof |
| NLI score (`0–1`) | Evidence/NLI | Confidence returned by OpenAI NLI or deterministic heuristic for a specific claim–passage relation | Overall answer certainty |
| Retrieval score | Hybrid retriever | Rank signal after semantic, keyword, authority logic | Probability that a passage is true |
| Overall answer confidence (`0–100`) | Synthesis | Share of verified query-time claims marked `SUPPORTED`, with fallback policy | Statistically calibrated probability |
| UI confidence | `frontend/src/utils/confidence.js` | Normalizes either ratio or percent and clamps to 0–100 for display | A new semantic score |

The confidence normalization prevents the common bug of rendering an already-percent value such as `94.1` as `9410%`:

```javascript
// frontend/src/utils/confidence.js — conceptually
const percentage = raw >= 0 && raw <= 1 ? raw * 100 : raw;
return Math.max(0, Math.min(100, percentage));
```

## 12. Security, tenancy, deployment, and performance

### 12.1 Isolation and authentication

- Authentication is centralized in `app.api.auth`; production mode expects verified Bearer JWTs, while development mode exists only for local convenience.
- The API checks workspace ownership before every workspace read or mutation.
- User knowledge records are scoped by workspace; queries never intentionally retrieve chunks from another workspace.
- Browser CORS must explicitly allow the deployed Vercel frontend origin.

### 12.2 Persistence

- **Local:** SQLite with foreign keys and WAL mode.
- **Production durable mode:** Postgres when `DATABASE_URL` is set.
- **Important Render caveat:** local SQLite inside an ephemeral Render web instance does not guarantee persistence across rebuilds/restarts. The storage endpoint exposes whether durable Postgres is active.

### 12.3 Low-latency design choices already implemented

- Lazy specialist construction: registry creates a specialist only when selected.
- Lazy OpenAI client creation: health checks do not load model clients.
- Chunk embeddings persist; only the query is normally embedded per retrieval.
- Single-query embeddings are cached in a bounded in-memory LRU-style map.
- Retrieval remains NumPy dot products; no PyTorch, Transformers, spaCy, sentence-transformers, or runtime FAISS dependency is required by the production workspace path.
- Comparison intentionally avoids claim/NLI work.
- The browser uses the latest SSE status line instead of rendering a large event log during a query.

## 13. Interview-ready theory questions and answers

### What is RAG, and why use it here?

RAG retrieves source passages before generation. It narrows the model context to documents relevant to the user's question and makes source excerpts available for review. In TrustLens, RAG is workspace-scoped, so a question is answered from that user's workspace rather than a global web corpus.

### Does RAG eliminate hallucinations?

No. RAG reduces the chance of unsupported generation by supplying relevant evidence, but retrieval can miss a source, rank irrelevant context highly, or the generator can still overstate a passage. TrustLens adds claim extraction, NLI-style verification, evidence links, contradictions, and explicit unknowns as additional controls.

### What is the difference between retrieval confidence and factual confidence?

Retrieval score estimates relevance under the rank function. Evidence/NLI score estimates the relation of a claim to one passage. Neither is a calibrated probability that a statement is true in the world. The displayed overall percentage is support coverage among extracted query-time claims, not factual certainty.

### Why normalize vectors for cosine similarity?

For normalized vectors, the dot product equals cosine similarity. That makes rank comparison based on angle/similarity rather than vector magnitude: `cos(θ) = (a · b) / (||a|| ||b||)`, so normalized `a` and `b` yield `a · b`.

### Why add lexical matching if semantic embeddings exist?

Dense retrieval catches paraphrase and conceptual similarity; lexical overlap rewards exact names, policy terms, and identifiers that a user may care about. The small capped boost is a simple hybrid strategy. It is not BM25, reciprocal-rank fusion, reranking, or learned-to-rank.

### Why weight authority levels?

The user can declare a source `HIGH`, `MEDIUM`, or `LOW`. Weighting lets otherwise comparable passages from more authoritative sources surface first. It is a transparent policy input—not automated source credibility verification—and should be explainable to the user.

### What is NLI in this design?

Natural language inference classifies a premise–hypothesis pair as entailment, contradiction, or neutral. Here a retrieved passage is the premise and an extracted claim is the hypothesis. The Evidence Specialist uses those labels to assign support status and retain the exact passage.

### Why keep a neutral class?

Because lack of support is not contradiction. A passage may be unrelated or incomplete. Collapsing neutral into false would make absence of evidence look like evidence of absence.

### Why split an answer into atomic claims?

One paragraph can mix several assertions, qualifiers, and conclusions. Claim-level verification lets the UI say which assertion is supported, contradicted, partially supported, or unproven rather than assigning one blanket verdict to a whole answer.

### Why use deterministic fallbacks?

They maintain availability when credentials, quota, or network access fail. The tradeoff is quality: feature hashing and lexical NLI are weaker than model-backed semantic methods. A trustworthy system labels this degraded mode in operations/documentation rather than claiming equivalent intelligence.

### Is the planner an agentic system?

It is agent-like in the limited architectural sense that it selects specialized modules based on intent and aggregates their outputs. It is not an autonomous multi-process system: the active workspace specialists are local async Python methods in one API process, and their routing is deterministic keyword logic.

### What is the purpose of the answer contract?

It turns an answer from a single uninspectable string into a review object: answer, confidence, verified claims, evidence, contradictions, assumptions, unknowns, related entities/events, plan trace, and latency. This makes uncertainty and provenance first-class UI data.

### Why use Server-Sent Events instead of WebSockets here?

The requirement is one-way server-to-browser progress plus one final result on top of a POST query. SSE is simpler, HTTP-friendly, and sufficient. WebSockets would be justified for bidirectional collaboration, cancellation/control channels, or long-lived multiplexed sessions, none of which the current query stream implements.

### What are the main recall and precision risks?

Recall can suffer from paragraph-only chunks, top-6 truncation, fallback embeddings, and keyword intent routing. Precision can suffer from broad passages, heuristic entity/contradiction patterns, authority self-declaration, or lexical fallback NLI. Reviewable citations and “insufficient evidence” are mitigation mechanisms, not proof that errors cannot occur.

### What would you improve next?

Strong next steps include token-aware overlapping chunks with document/page coordinates, a real hybrid sparse ranker (BM25) plus reranking, semantic intent classification, explicit degradation metadata, calibrated confidence evaluation, persistent relationship writes, asynchronous job/cancellation support, document MIME parsing/OCR with security controls, and evaluation sets that measure retrieval recall and claim-verification precision/recall.

## 14. Honest limitations to state in a demo or interview

1. **Authority is declared by the workspace user.** The system prioritizes it but does not authenticate a source's real-world authority.
2. **Entity and timeline extraction are regex/rule based.** They are transparent and lightweight but not comprehensive NER or temporal parsing.
3. **Comparison analyzes two top retrieved passages, not full document diffs.**
4. **Some specialist confidences are fixed heuristics.** They are not calibration-backed probabilities.
5. **Fallback NLI is lexical.** It should not be represented as equivalent to a trained semantic NLI model.
6. **The system's core guarantee is evidence traceability, not objective truth certification.**
7. **The current SSE stream is progress plus final result, not a background durable pipeline.**
8. **Uploaded content is text-based in the current route contract.** Robust binary PDF/DOCX/OCR ingestion would be a future expansion rather than an existing claim.

## 15. Practical code-reading path

For a technical walkthrough, read in this order:

1. [frontend/src/App.jsx](../frontend/src/App.jsx) — user-facing state and page composition.
2. [frontend/src/api.js](../frontend/src/api.js) — browser request/SSE contract.
3. [backend/app/api/routes.py](../backend/app/api/routes.py) — route boundaries and ownership checks.
4. [backend/app/specialists/ingestion_agent.py](../backend/app/specialists/ingestion_agent.py) — document-to-record transformation.
5. [backend/app/knowledge/db.py](../backend/app/knowledge/db.py) and [repository.py](../backend/app/knowledge/repository.py) — durable model.
6. [backend/app/knowledge/hybrid_retriever.py](../backend/app/knowledge/hybrid_retriever.py) — workspace retrieval.
7. [backend/app/planner/planner.py](../backend/app/planner/planner.py) — selective specialist orchestration.
8. [backend/app/specialists/evidence_agent.py](../backend/app/specialists/evidence_agent.py) and [models/nli.py](../backend/app/models/nli.py) — claim verification.
9. [backend/app/specialists/synthesis_agent.py](../backend/app/specialists/synthesis_agent.py) — answer contract synthesis.
10. [tests/test_query_stream.py](../tests/test_query_stream.py) and [tests/test_planner_dispatch.py](../tests/test_planner_dispatch.py) — behavior guarantees for streaming and selective dispatch.

## 16. Verification references

The repository's test suite includes targeted regression coverage for:

- SSE event content type, stage events, and final result event.
- Comparison dispatch skipping Claim Detective and Evidence Specialist.
- Storage, ownership, security, persistence, analytics, pipeline, retrieval concurrency, and specialist registry behavior.

Run the relevant checks from the repository root:

```powershell
pytest tests -q
```

Run frontend checks from `frontend`:

```powershell
npm test
npm run build
```

## 17. Intelligence graph update

TrustLens now projects the canonical workspace record into additive
`graph_nodes` and `graph_edges` tables. The graph is not a separate source of
truth: documents, claims, evidence, entities, events, relationships, and
dataset profiles remain canonical. Edges preserve method, confidence, source
document/chunk references, and an explanation. The browser renders this
projection with Sigma and Graphology, while filters and inspection state remain
in React.

The query verification path now exposes NLI provider/fallback provenance,
deterministic numeric checks, temporal update/conflict checks, cross-source
counts, and an evidence support score. That score is deliberately not an
objective truth probability. See [INTELLIGENCE_GRAPH.md](INTELLIGENCE_GRAPH.md)
for the graph contract and implementation details.

---

**One-sentence interview summary:** TrustLens is a workspace-scoped evidence intelligence system that persists a reviewable source record, uses hybrid retrieval to identify relevant passages, selectively dispatches deterministic and optional model-backed specialists, verifies claims against evidence, and returns uncertainty and provenance alongside each answer.
