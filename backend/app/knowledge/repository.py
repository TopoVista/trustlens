"""Data access repository for TrustLens Knowledge and Evidence Graph"""
import json
import uuid
from typing import Any, Dict, List, Optional, Tuple
from app.knowledge.db import get_db_connection


class KnowledgeRepository:
    """
    Thread-safe repository for all workspace-scoped knowledge operations.
    Enforces strict workspace isolation across all data objects.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _get_conn(self):
        return get_db_connection(self.db_path)

    # --- 1. Workspace Operations ---

    def create_workspace(self, name: str, description: str = "") -> Dict[str, Any]:
        workspace_id = f"ws_{uuid.uuid4().hex[:12]}"
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO workspaces (id, name, description) VALUES (?, ?, ?)",
                (workspace_id, name, description)
            )
        return self.get_workspace(workspace_id)

    def get_workspace(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
            return dict(row) if row else None

    def list_workspaces(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM workspaces ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def ensure_default_workspace(self) -> str:
        """Ensures at least one default workspace exists."""
        workspaces = self.list_workspaces()
        if workspaces:
            return workspaces[0]["id"]
        created = self.create_workspace("Personal Knowledge", "Default user intelligence workspace")
        return created["id"]

    # --- 2. Document & Chunk Operations ---

    def add_document(
        self,
        workspace_id: str,
        title: str,
        filename: str,
        file_type: str,
        raw_content: str,
        authority_level: str = "MEDIUM",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        meta_str = json.dumps(metadata or {})
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO documents (id, workspace_id, title, filename, file_type, raw_content, authority_level, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (doc_id, workspace_id, title, filename, file_type, raw_content, authority_level, meta_str)
            )
        return doc_id

    def add_chunks(self, chunks_data: List[Dict[str, Any]]) -> None:
        """Batch inserts document chunks with precise location references."""
        with self._get_conn() as conn:
            for c in chunks_data:
                chunk_id = c.get("id") or f"chk_{uuid.uuid4().hex[:12]}"
                conn.execute(
                    """
                    INSERT INTO chunks (id, workspace_id, document_id, chunk_index, text, location_info)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (chunk_id, c["workspace_id"], c["document_id"], c["chunk_index"], c["text"], c.get("location_info", ""))
                )

    def get_documents(self, workspace_id: str) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM documents WHERE workspace_id = ? ORDER BY created_at DESC",
                (workspace_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_document(self, workspace_id: str, doc_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE workspace_id = ? AND id = ?",
                (workspace_id, doc_id)
            ).fetchone()
            return dict(row) if row else None

    def get_chunks(self, workspace_id: str, doc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            if doc_id:
                rows = conn.execute(
                    "SELECT * FROM chunks WHERE workspace_id = ? AND document_id = ? ORDER BY chunk_index ASC",
                    (workspace_id, doc_id)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM chunks WHERE workspace_id = ? ORDER BY created_at DESC LIMIT 500",
                    (workspace_id,)
                ).fetchall()
            return [dict(r) for r in rows]

    # --- Chunk embeddings (lightweight persistent vector store) ---

    def set_chunk_embedding(
        self,
        workspace_id: str,
        chunk_id: str,
        embedding_bytes: bytes,
        dim: int,
        model: str,
    ) -> None:
        """Upserts a persisted embedding vector (float32 bytes) for a chunk."""
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO chunk_embeddings (chunk_id, workspace_id, embedding, dim, model)
                VALUES (?, ?, ?, ?, ?)
                """,
                (chunk_id, workspace_id, embedding_bytes, int(dim), model),
            )

    def get_chunk_embeddings(self, workspace_id: str) -> Dict[str, Tuple[Any, str]]:
        """Returns {chunk_id: (embedding vector, model_name)} for a workspace.

        Embedding vectors are decoded from float32 BLOBs into numpy arrays so
        the retrieval layer can use NumPy dot products directly.
        """
        import numpy as np

        result: Dict[str, Tuple[Any, str]] = {}
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT chunk_id, embedding, model FROM chunk_embeddings WHERE workspace_id = ?",
                (workspace_id,),
            ).fetchall()
        for r in rows:
            result[r["chunk_id"]] = (np.frombuffer(bytes(r["embedding"]), dtype=np.float32).copy(), r["model"])
        return result

    # --- 3. Entities & Relationships ---

    def add_entity(self, workspace_id: str, name: str, entity_type: str, aliases: Optional[List[str]] = None) -> str:
        norm = name.lower().strip()
        with self._get_conn() as conn:
            existing = conn.execute(
                "SELECT id FROM entities WHERE workspace_id = ? AND normalized_name = ?",
                (workspace_id, norm)
            ).fetchone()
            if existing:
                return existing["id"]

            entity_id = f"ent_{uuid.uuid4().hex[:10]}"
            conn.execute(
                """
                INSERT INTO entities (id, workspace_id, name, normalized_name, entity_type, aliases_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (entity_id, workspace_id, name, norm, entity_type, json.dumps(aliases or []))
            )
            return entity_id

    def add_relationship(
        self,
        workspace_id: str,
        source_entity_id: str,
        target_entity_id: str,
        relation_type: str,
        evidence_text: str = ""
    ) -> str:
        rel_id = f"rel_{uuid.uuid4().hex[:10]}"
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO relationships (id, workspace_id, source_entity_id, target_entity_id, relation_type, evidence_text)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (rel_id, workspace_id, source_entity_id, target_entity_id, relation_type, evidence_text)
            )
        return rel_id

    def get_entities(self, workspace_id: str) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM entities WHERE workspace_id = ? ORDER BY name ASC",
                (workspace_id,)
            ).fetchall()
            result = []
            for r in rows:
                item = dict(r)
                item["aliases"] = json.loads(item["aliases_json"])
                result.append(item)
            return result

    def get_knowledge_graph(self, workspace_id: str) -> Dict[str, Any]:
        with self._get_conn() as conn:
            entities = self.get_entities(workspace_id)
            rel_rows = conn.execute(
                """
                SELECT r.id, r.relation_type, r.evidence_text,
                       s.name as source_name, s.entity_type as source_type,
                       t.name as target_name, t.entity_type as target_type
                FROM relationships r
                JOIN entities s ON r.source_entity_id = s.id
                JOIN entities t ON r.target_entity_id = t.id
                WHERE r.workspace_id = ?
                """,
                (workspace_id,)
            ).fetchall()
            return {
                "nodes": [{"id": e["id"], "name": e["name"], "type": e["entity_type"]} for e in entities],
                "edges": [dict(r) for r in rel_rows]
            }

    # --- 4. Claim & Evidence Graph ---

    def add_claim(
        self,
        workspace_id: str,
        statement: str,
        document_id: Optional[str] = None,
        claim_type: str = "FACTUAL",
        status: str = "UNRESOLVED",
        confidence: float = 0.5
    ) -> str:
        claim_id = f"clm_{uuid.uuid4().hex[:10]}"
        norm = statement.lower().strip()
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO claims (id, workspace_id, document_id, statement, normalized_statement, claim_type, status, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (claim_id, workspace_id, document_id, statement, norm, claim_type, status, confidence)
            )
        return claim_id

    def add_evidence(
        self,
        workspace_id: str,
        claim_id: str,
        document_id: str,
        exact_passage: str,
        location_ref: str,
        relationship_type: str = "SUPPORTS",
        strength: float = 0.8,
        explanation: str = "",
        chunk_id: Optional[str] = None
    ) -> str:
        ev_id = f"ev_{uuid.uuid4().hex[:10]}"
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO evidence (id, workspace_id, claim_id, document_id, chunk_id, exact_passage, location_ref, relationship_type, strength, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (ev_id, workspace_id, claim_id, document_id, chunk_id, exact_passage, location_ref, relationship_type, strength, explanation)
            )
        return ev_id

    def update_claim_status(self, claim_id: str, status: str, confidence: float) -> None:
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE claims SET status = ?, confidence = ? WHERE id = ?",
                (status, confidence, claim_id)
            )

    def get_claims(self, workspace_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT c.*, d.title as document_title, d.filename
                FROM claims c
                LEFT JOIN documents d ON c.document_id = d.id
                WHERE c.workspace_id = ?
                ORDER BY c.created_at DESC LIMIT ?
                """,
                (workspace_id, limit)
            ).fetchall()
            claims = []
            for r in rows:
                c = dict(r)
                # Fetch linked evidence
                ev_rows = conn.execute(
                    "SELECT * FROM evidence WHERE claim_id = ?",
                    (c["id"],)
                ).fetchall()
                c["evidence"] = [dict(ev) for ev in ev_rows]
                claims.append(c)
            return claims

    def get_contradictions(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Returns all claims that have contradicting evidence attached."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT c.id as claim_id, c.statement, c.status,
                       e.id as evidence_id, e.exact_passage, e.location_ref, e.explanation,
                       d.title as source_title, d.authority_level
                FROM evidence e
                JOIN claims c ON e.claim_id = c.id
                JOIN documents d ON e.document_id = d.id
                WHERE e.workspace_id = ? AND (e.relationship_type = 'CONTRADICTS' OR c.status = 'CONTRADICTED')
                """,
                (workspace_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    # --- 5. Timeline Events ---

    def add_event(
        self,
        workspace_id: str,
        title: str,
        date_str: str,
        description: str = "",
        document_id: Optional[str] = None,
        location_ref: str = "",
        timestamp_val: Optional[float] = None
    ) -> str:
        ev_id = f"evt_{uuid.uuid4().hex[:10]}"
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO events (id, workspace_id, document_id, title, date_str, timestamp_val, description, location_ref)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (ev_id, workspace_id, document_id, title, date_str, timestamp_val, description, location_ref)
            )
        return ev_id

    def get_timeline(self, workspace_id: str) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT e.*, d.title as document_title
                FROM events e
                LEFT JOIN documents d ON e.document_id = d.id
                WHERE e.workspace_id = ?
                ORDER BY e.date_str ASC, e.timestamp_val ASC
                """,
                (workspace_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    # --- 6. User-Defined Semantic Rules ---

    def add_semantic_rule(self, workspace_id: str, rule_type: str, rule_key: str, rule_value: str) -> str:
        rule_id = f"rule_{uuid.uuid4().hex[:10]}"
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO semantic_rules (id, workspace_id, rule_type, rule_key, rule_value)
                VALUES (?, ?, ?, ?, ?)
                """,
                (rule_id, workspace_id, rule_type, rule_key, rule_value)
            )
        return rule_id

    def get_semantic_rules(self, workspace_id: str) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM semantic_rules WHERE workspace_id = ? ORDER BY created_at ASC",
                (workspace_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    # --- 7. Data Analyst: Dataset Profiles ---

    def add_dataset_profile(
        self,
        workspace_id: str,
        document_id: str,
        row_count: int,
        col_count: int,
        columns: List[str],
        profile: Dict[str, Any],
        insights: List[Dict[str, Any]]
    ) -> str:
        pid = f"dsp_{uuid.uuid4().hex[:10]}"
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO dataset_profiles (id, workspace_id, document_id, row_count, col_count, columns_json, profile_json, insights_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (pid, workspace_id, document_id, row_count, col_count, json.dumps(columns), json.dumps(profile), json.dumps(insights))
            )
        return pid

    def get_dataset_profiles(self, workspace_id: str) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT p.*, d.title, d.filename
                FROM dataset_profiles p
                JOIN documents d ON p.document_id = d.id
                WHERE p.workspace_id = ?
                ORDER BY p.created_at DESC
                """,
                (workspace_id,)
            ).fetchall()
            result = []
            for r in rows:
                item = dict(r)
                item["columns"] = json.loads(item["columns_json"])
                item["profile"] = json.loads(item["profile_json"])
                item["insights"] = json.loads(item["insights_json"])
                result.append(item)
            return result

    # --- 8. Knowledge Health Calculator ---

    def get_knowledge_health(self, workspace_id: str) -> Dict[str, Any]:
        """Calculates authentic workspace intelligence metrics from stored objects."""
        with self._get_conn() as conn:
            doc_count = conn.execute("SELECT COUNT(*) FROM documents WHERE workspace_id = ?", (workspace_id,)).fetchone()[0]
            claim_count = conn.execute("SELECT COUNT(*) FROM claims WHERE workspace_id = ?", (workspace_id,)).fetchone()[0]
            entity_count = conn.execute("SELECT COUNT(*) FROM entities WHERE workspace_id = ?", (workspace_id,)).fetchone()[0]
            event_count = conn.execute("SELECT COUNT(*) FROM events WHERE workspace_id = ?", (workspace_id,)).fetchone()[0]
            evidence_count = conn.execute("SELECT COUNT(*) FROM evidence WHERE workspace_id = ?", (workspace_id,)).fetchone()[0]

            # Claims status breakdown
            supported = conn.execute("SELECT COUNT(*) FROM claims WHERE workspace_id = ? AND status = 'SUPPORTED'", (workspace_id,)).fetchone()[0]
            partially_supported = conn.execute("SELECT COUNT(*) FROM claims WHERE workspace_id = ? AND status = 'PARTIALLY_SUPPORTED'", (workspace_id,)).fetchone()[0]
            contradicted = conn.execute("SELECT COUNT(*) FROM claims WHERE workspace_id = ? AND status = 'CONTRADICTED'", (workspace_id,)).fetchone()[0]
            unsupported = conn.execute("SELECT COUNT(*) FROM claims WHERE workspace_id = ? AND (status = 'UNSUPPORTED' OR status = 'UNRESOLVED')", (workspace_id,)).fetchone()[0]

            supported_pct = round((supported / claim_count * 100), 1) if claim_count > 0 else 0.0
            partially_supported_pct = round((partially_supported / claim_count * 100), 1) if claim_count > 0 else 0.0
            contradicted_pct = round((contradicted / claim_count * 100), 1) if claim_count > 0 else 0.0
            unsupported_pct = round((unsupported / claim_count * 100), 1) if claim_count > 0 else 0.0

            contradiction_count = len(self.get_contradictions(workspace_id))
            gaps_count = unsupported

            return {
                "documents": doc_count,
                "claims": claim_count,
                "entities": entity_count,
                "events": event_count,
                "evidence_links": evidence_count,
                "breakdown": {
                    "supported": supported,
                    "supported_pct": supported_pct,
                    "partially_supported": partially_supported,
                    "partially_supported_pct": partially_supported_pct,
                    "contradicted": contradicted,
                    "contradicted_pct": contradicted_pct,
                    "unresolved_unsupported": unsupported,
                    "unresolved_unsupported_pct": unsupported_pct
                },
                "major_contradictions": contradiction_count,
                "knowledge_gaps": gaps_count
            }

    # --- 9. Proactive Discoveries ("Things You Should Know") ---

    def get_proactive_discoveries(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Surfaces non-obvious conflicts, unsupported assumptions, and key insights."""
        discoveries = []
        with self._get_conn() as conn:
            # Check 1: Contradictions across documents
            contra_rows = conn.execute(
                """
                SELECT c.statement, e.exact_passage, d.title as doc_title, e.explanation
                FROM evidence e
                JOIN claims c ON e.claim_id = c.id
                JOIN documents d ON e.document_id = d.id
                WHERE e.workspace_id = ? AND e.relationship_type = 'CONTRADICTS'
                LIMIT 3
                """,
                (workspace_id,)
            ).fetchall()
            for r in contra_rows:
                discoveries.append({
                    "type": "contradiction",
                    "title": "Conflicting Information Identified",
                    "severity": "WARNING",
                    "summary": f"Conflict detected for assertion: \"{r['statement']}\"",
                    "evidence": r["exact_passage"],
                    "source": r["doc_title"],
                    "detail": r["explanation"] or "Passages present opposing statements or metrics."
                })

            # Check 2: Major unsupported strategic claims
            unsupp_rows = conn.execute(
                """
                SELECT c.statement, d.title as doc_title
                FROM claims c
                JOIN documents d ON c.document_id = d.id
                WHERE c.workspace_id = ? AND (c.status = 'UNSUPPORTED' OR c.status = 'UNRESOLVED')
                ORDER BY LENGTH(c.statement) DESC LIMIT 2
                """,
                (workspace_id,)
            ).fetchall()
            for r in unsupp_rows:
                discoveries.append({
                    "type": "gap",
                    "title": "Unsupported Assertion in Workspace",
                    "severity": "NOTICE",
                    "summary": f"Key claim lacks evidentiary backing: \"{r['statement']}\"",
                    "evidence": "No supporting document passage identified.",
                    "source": r["doc_title"],
                    "detail": "Consider uploading supporting documentation to verify this assertion."
                })

            # Check 3: Dataset insights (from Data Analyst)
            profiles = self.get_dataset_profiles(workspace_id)
            for p in profiles[:2]:
                for ins in p.get("insights", [])[:1]:
                    discoveries.append({
                        "type": "data_insight",
                        "title": f"Dataset Statistical Pattern: {p['title']}",
                        "severity": "INSIGHT",
                        "summary": ins.get("finding", "Statistical pattern extracted from structured table."),
                        "evidence": ins.get("provenance", f"{p['row_count']} rows analyzed in {p['filename']}"),
                        "source": p["filename"],
                        "detail": ins.get("implication", "Analyzed by Data Analyst specialist.")
                    })

        return discoveries
