"""Build a normalized, evidence-backed graph projection from canonical records."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.knowledge.repository import KnowledgeRepository


class GraphBuilder:
    """Maintains graph nodes/edges without replacing the canonical domain tables."""

    def __init__(self, repo: Optional[KnowledgeRepository] = None):
        self.repo = repo or KnowledgeRepository()

    def rebuild_workspace(self, workspace_id: str) -> Dict[str, int]:
        """Idempotently project current workspace records into the graph tables."""
        nodes_before = self.repo.get_graph_stats(workspace_id)["nodes"]
        edges_before = self.repo.get_graph_stats(workspace_id)["edges"]
        node_ids: Dict[tuple[str, str], str] = {}

        def add_node(node_type: str, label: str, reference_type: str, reference_id: str, metadata: Dict[str, Any]) -> str:
            node_id = self.repo.upsert_graph_node(workspace_id, node_type, label, reference_type, reference_id, metadata)
            node_ids[(reference_type, reference_id)] = node_id
            return node_id

        documents = self.repo.get_documents(workspace_id)
        for document in documents:
            add_node("DOCUMENT", document["title"], "document", document["id"], {
                "filename": document.get("filename", ""),
                "authority_level": document.get("authority_level", "MEDIUM"),
                "ingestion_status": document.get("ingestion_status", "READY"),
            })

        entities = self.repo.get_entities(workspace_id)
        for entity in entities:
            add_node("ENTITY", entity["name"], "entity", entity["id"], {
                "entity_type": entity.get("entity_type", "Concept"),
                "aliases": entity.get("aliases", []),
            })

        events = self.repo.get_timeline(workspace_id)
        for event in events:
            event_node = add_node("EVENT", event["title"], "event", event["id"], {
                "date_str": event.get("date_str", ""),
                "timestamp": event.get("timestamp_val"),
                "description": event.get("description", ""),
            })
            document_node = node_ids.get(("document", event.get("document_id", "")))
            if document_node:
                self.repo.upsert_graph_edge(workspace_id, event_node, document_node, "REPORTED_BY", 0.95,
                                            "EXPLICIT_SOURCE_RELATION", event.get("document_id"), None,
                                            "Event extracted from this source document.")

        for first, second in zip(events, events[1:]):
            first_node = node_ids.get(("event", first["id"]))
            second_node = node_ids.get(("event", second["id"]))
            if first_node and second_node and first.get("timestamp_val") is not None and second.get("timestamp_val") is not None:
                self.repo.upsert_graph_edge(workspace_id, first_node, second_node, "PRECEDES", 0.8, "TEMPORAL",
                                            second.get("document_id"), None, "Dates establish this ordering.")

        claims = self.repo.get_claims(workspace_id)
        claim_nodes: Dict[str, str] = {}
        for claim in claims:
            claim_node = add_node("CLAIM", claim["statement"], "claim", claim["id"], {
                "status": claim.get("status", "UNRESOLVED"),
                "confidence": claim.get("confidence", 0.0),
                "claim_type": claim.get("claim_type", "FACTUAL"),
                "document_id": claim.get("document_id"),
            })
            claim_nodes[claim["id"]] = claim_node
            document_node = node_ids.get(("document", claim.get("document_id", "")))
            if document_node:
                self.repo.upsert_graph_edge(workspace_id, claim_node, document_node, "REPORTED_BY", 0.95,
                                            "EXPLICIT_SOURCE_RELATION", claim.get("document_id"), None,
                                            "Claim was extracted from this document.")

            statement = claim.get("statement", "").lower()
            for entity in entities:
                aliases = [entity.get("name", ""), *entity.get("aliases", [])]
                if any(alias and str(alias).lower() in statement for alias in aliases):
                    entity_node = node_ids.get(("entity", entity["id"]))
                    if entity_node:
                        self.repo.upsert_graph_edge(workspace_id, claim_node, entity_node, "MENTIONS", 0.9,
                                                    "EXPLICIT_SOURCE_RELATION", claim.get("document_id"), None,
                                                    "Entity name occurs in the extracted claim.")

            for evidence in claim.get("evidence", []):
                evidence_id = evidence["id"]
                evidence_node = add_node("EVIDENCE", evidence.get("exact_passage", "Evidence passage")[:160], "evidence", evidence_id, {
                    "passage": evidence.get("exact_passage", ""),
                    "location": evidence.get("location_ref", ""),
                    "strength": evidence.get("strength", 0.0),
                    "relationship_type": evidence.get("relationship_type", "SUPPORTS"),
                    "document_id": evidence.get("document_id"),
                    "chunk_id": evidence.get("chunk_id"),
                })
                relation = "CONTRADICTS" if evidence.get("relationship_type") == "CONTRADICTS" else "SUPPORTED_BY"
                self.repo.upsert_graph_edge(workspace_id, claim_node, evidence_node, relation,
                                            evidence.get("strength", 0.0), "NLI",
                                            evidence.get("document_id"), evidence.get("chunk_id"),
                                            evidence.get("explanation", "Claim-to-evidence verification link."))
                evidence_document_node = node_ids.get(("document", evidence.get("document_id", "")))
                if evidence_document_node:
                    self.repo.upsert_graph_edge(workspace_id, evidence_node, evidence_document_node, "REPORTED_BY",
                                                0.95, "EXPLICIT_SOURCE_RELATION", evidence.get("document_id"),
                                                evidence.get("chunk_id"), "Evidence passage belongs to this document.")

        # A claim-to-claim contradiction is projected only when an existing
        # contradictory evidence passage has meaningful lexical support for a
        # claim from its source document. This avoids decorative claim links.
        for claim in claims:
            claim_node = claim_nodes.get(claim["id"])
            if not claim_node:
                continue
            for evidence in claim.get("evidence", []):
                if evidence.get("relationship_type") != "CONTRADICTS":
                    continue
                passage_tokens = set(re.findall(r"[a-z0-9]+", evidence.get("exact_passage", "").lower()))
                for other in claims:
                    if other["id"] == claim["id"] or other.get("document_id") != evidence.get("document_id"):
                        continue
                    statement_tokens = set(re.findall(r"[a-z0-9]+", other.get("statement", "").lower()))
                    overlap = len(passage_tokens & statement_tokens) / max(1, len(statement_tokens))
                    other_node = claim_nodes.get(other["id"])
                    if other_node and overlap >= 0.5:
                        self.repo.upsert_graph_edge(workspace_id, claim_node, other_node, "CONTRADICTS",
                                                    evidence.get("strength", 0.0), "NLI",
                                                    evidence.get("document_id"), evidence.get("chunk_id"),
                                                    "A contradictory evidence passage also supports this source claim.")

        for relationship in self.repo.get_knowledge_graph(workspace_id).get("edges", []):
            source_name = relationship.get("source_name")
            target_name = relationship.get("target_name")
            source = next((entity for entity in entities if entity["name"] == source_name), None)
            target = next((entity for entity in entities if entity["name"] == target_name), None)
            if not source or not target:
                continue
            source_node = node_ids.get(("entity", source["id"]))
            target_node = node_ids.get(("entity", target["id"]))
            if source_node and target_node:
                relation = relationship.get("relation_type", "ASSOCIATED_WITH")
                confidence = 0.55 if relation == "ASSOCIATED_WITH" else 0.84
                self.repo.upsert_graph_edge(workspace_id, source_node, target_node, relation, confidence,
                                            "EXPLICIT_SOURCE_RELATION" if relation != "ASSOCIATED_WITH" else "HEURISTIC",
                                            None, None, relationship.get("evidence_text", ""))

        for profile in self.repo.get_dataset_profiles(workspace_id):
            dataset_node = add_node("DATASET", profile.get("title") or profile.get("filename", "Dataset"),
                                    "dataset", profile["id"], {"document_id": profile["document_id"],
                                                                 "rows": profile.get("row_count"), "columns": profile.get("col_count")})
            document_node = node_ids.get(("document", profile.get("document_id", "")))
            if document_node:
                self.repo.upsert_graph_edge(workspace_id, dataset_node, document_node, "DERIVED_FROM", 1.0,
                                            "STRUCTURED_DATA", profile["document_id"], None,
                                            "Dataset profile was calculated from this document.")
            numeric = []
            for column, column_profile in profile.get("profile", {}).items():
                if not isinstance(column_profile, dict) or column_profile.get("type") != "Numeric":
                    continue
                variable_node = add_node("VARIABLE", column, "dataset_variable", f"{profile['id']}:{column}", {
                    "dataset_id": profile["id"], "column": column, "stats": column_profile.get("stats", {}),
                })
                numeric.append((column, variable_node))
                self.repo.upsert_graph_edge(workspace_id, variable_node, dataset_node, "PART_OF", 1.0,
                                            "STRUCTURED_DATA", profile["document_id"], None,
                                            "Numeric column in this dataset.")
                stats = column_profile.get("stats", {})
                if "mean" in stats:
                    value_node = add_node("VALUE", f"{column} mean: {stats['mean']}", "dataset_value",
                                          f"{profile['id']}:{column}:mean", {
                                              "dataset_id": profile["id"], "column": column, "measure": "mean", "value": stats["mean"],
                                          })
                    self.repo.upsert_graph_edge(workspace_id, variable_node, value_node, "HAS_VALUE", 1.0,
                                                "STRUCTURED_DATA", profile["document_id"], None,
                                                "Mean calculated from the source dataset.")
            for correlation in profile.get("correlations", profile.get("profile", {}).get("__correlations__", [])):
                first = node_ids.get(("dataset_variable", f"{profile['id']}:{correlation.get('column_a')}"))
                second = node_ids.get(("dataset_variable", f"{profile['id']}:{correlation.get('column_b')}"))
                if first and second:
                    coefficient = float(correlation.get("coefficient", 0.0))
                    self.repo.upsert_graph_edge(workspace_id, first, second, "CORRELATED_WITH", abs(coefficient),
                                                "STRUCTURED_DATA", profile["document_id"], None,
                                                "Pearson correlation is association only; it does not establish causation.",
                                                {"coefficient": coefficient, "sample_size": correlation.get("sample_size"),
                                                 "method": "pearson"})

        stats = self.repo.get_graph_stats(workspace_id)
        return {"nodes": stats["nodes"], "edges": stats["edges"],
                "nodes_created": max(0, stats["nodes"] - nodes_before),
                "edges_created": max(0, stats["edges"] - edges_before)}
