# TrustLens Intelligence Graph

## Purpose

The intelligence graph is a normalized, inspectable projection of an authorized
workspace. It does not replace canonical storage and it does not invent
relationships to make the visualization denser.

```text
document ──REPORTED_BY── claim ──SUPPORTED_BY / CONTRADICTS── evidence
   │                         │                                  │
   ├──REPORTED_BY── event     └──MENTIONS── entity                └──REPORTED_BY── document
   └──DERIVED_FROM── dataset ──PART_OF── variable ──HAS_VALUE── value
                                              └──CORRELATED_WITH── variable
```

## Persistence

`graph_nodes` uses one stable node per `(workspace_id, reference_type,
reference_id)`. `graph_edges` is idempotent by source, target, relation, and
evidence references. It includes:

- `confidence` in `[0, 1]`
- `provenance_type`: `NLI`, `NUMERIC`, `TEMPORAL`, `STRUCTURED_DATA`,
  `EXPLICIT_SOURCE_RELATION`, or `HEURISTIC`
- optional source document and chunk IDs
- explanation and metadata

SQLite and Postgres receive the same additive `CREATE TABLE IF NOT EXISTS`
migration in `app.knowledge.db.ensure_schema`.

## API contract

### `GET /api/workspaces/{workspace_id}/graph`

Optional parameters: `mode`, `min_confidence`, `document_id`, and `limit`.

```json
{
  "nodes": [{
    "id": "gn_…",
    "type": "CLAIM",
    "label": "Revenue grew 18%.",
    "reference_type": "claim",
    "reference_id": "clm_…",
    "status": "SUPPORTED",
    "confidence": 0.91,
    "metadata": {}
  }],
  "edges": [{
    "id": "ge_…",
    "source": "gn_…",
    "target": "gn_…",
    "relation": "SUPPORTED_BY",
    "confidence": 0.91,
    "explanation": "Claim-to-evidence verification link.",
    "provenance": {"method": "NLI", "document_id": "doc_…", "chunk_id": "chk_…", "metadata": {}}
  }],
  "stats": {"nodes": 12, "edges": 16, "claims": 3, "contradictions": 1}
}
```

`GET /graph/nodes/{node_id}` and `GET /graph/path?source=&target=` provide
node provenance and a confidence-prioritized evidence-backed path. Every
endpoint enforces workspace ownership before reading a node or edge.

## Verification signals

For each compact reranked evidence candidate, TrustLens records NLI label,
provider/model, fallback status, numeric validation, and temporal validation.
Numeric validation computes percentage changes when a source contains an
explicit before/after pair. Temporal validation treats explicit rescheduling or
revision language as `UPDATED_BY`, not automatically as contradiction.

The displayed support score combines authority, relevance, NLI, numeric and
temporal consistency, and cross-source agreement. It is explicitly an
**evidence support score**, not a probability of truth. Correlation graph edges
carry Pearson coefficient/sample metadata and never establish causation.

## Client behavior

The graph is rendered with Sigma (WebGL) and represented locally with
Graphology. React owns filters, selected nodes/edges, detail drawers, and
reasoning-path state. Hover highlights immediate neighbors without a network
request. Double-click or Focus animates the camera for 420 ms; reduced-motion
CSS disables long animation. The local guide uses a fixed target manifest and
can only spotlight or navigate to declared controls.
