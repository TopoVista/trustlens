"""Safe workspace-scoped graph query helpers."""
from __future__ import annotations

import heapq
import math
from typing import Any, Dict, List, Optional, Set

from app.knowledge.repository import KnowledgeRepository


_MODE_TYPES = {
    "all": set(), "claims": {"CLAIM"}, "entities": {"ENTITY"}, "variables": {"VARIABLE", "VALUE", "DATASET"},
    "evidence": {"EVIDENCE"}, "contradictions": {"CLAIM", "EVIDENCE", "EVENT", "DOCUMENT"},
    "dependencies": {"CLAIM", "ENTITY", "VARIABLE", "EVENT"}, "data": {"DATASET", "VARIABLE", "VALUE"},
}


class GraphQueries:
    def __init__(self, repo: Optional[KnowledgeRepository] = None):
        self.repo = repo or KnowledgeRepository()

    def graph(self, workspace_id: str, mode: str = "all", min_confidence: float = 0.5,
              document_id: Optional[str] = None, limit: int = 1000) -> Dict[str, Any]:
        mode = mode if mode in _MODE_TYPES else "all"
        node_types = _MODE_TYPES[mode]
        nodes = self.repo.get_graph_nodes(workspace_id, limit=limit)
        edges = self.repo.get_graph_edges(workspace_id, limit=max(limit * 4, 1000))
        if mode == "contradictions":
            contradiction_edges = [edge for edge in edges if edge["relation_type"] == "CONTRADICTS"]
            node_ids = {node_id for edge in contradiction_edges for node_id in (edge["source_node_id"], edge["target_node_id"])}
            nodes = [node for node in nodes if node["id"] in node_ids]
            edges = contradiction_edges
        else:
            if node_types:
                nodes = [node for node in nodes if node["node_type"] in node_types]
            if document_id:
                nodes = [node for node in nodes if node.get("metadata", {}).get("document_id") == document_id or node.get("reference_id") == document_id]
            node_ids = {node["id"] for node in nodes}
            edges = [edge for edge in edges if edge["source_node_id"] in node_ids and edge["target_node_id"] in node_ids]
        edges = [edge for edge in edges if edge["confidence"] >= min_confidence][:max(1, min(limit * 4, 5000))]
        connected = {node_id for edge in edges for node_id in (edge["source_node_id"], edge["target_node_id"])}
        nodes = [node for node in nodes if node["id"] in connected or node["node_type"] == "DOCUMENT"][:max(1, min(limit, 2000))]
        node_ids = {node["id"] for node in nodes}
        edges = [edge for edge in edges if edge["source_node_id"] in node_ids and edge["target_node_id"] in node_ids]
        return {"nodes": [self._public_node(node) for node in nodes], "edges": [self._public_edge(edge) for edge in edges],
                "stats": self.repo.get_graph_stats(workspace_id)}

    def node_detail(self, workspace_id: str, node_id: str) -> Optional[Dict[str, Any]]:
        node = self.repo.get_graph_node(workspace_id, node_id)
        if not node:
            return None
        edges = [edge for edge in self.repo.get_graph_edges(workspace_id) if node_id in {edge["source_node_id"], edge["target_node_id"]}]
        detail = self._public_node(node)
        detail["edges"] = [self._public_edge(edge) for edge in edges[:100]]
        detail["supporting_evidence_count"] = sum(1 for edge in edges if edge["relation_type"] in {"SUPPORTED_BY", "SUPPORTS"})
        detail["contradicting_evidence_count"] = sum(1 for edge in edges if edge["relation_type"] == "CONTRADICTS")
        detail["why_exists"] = "Projected from a workspace record and its evidence-backed connections."
        return detail

    def neighbors(self, workspace_id: str, node_id: str, depth: int = 1, limit: int = 160) -> Optional[Dict[str, Any]]:
        if not self.repo.get_graph_node(workspace_id, node_id):
            return None
        depth = 1 if int(depth) <= 1 else 2
        all_edges = self.repo.get_graph_edges(workspace_id)
        discovered: Set[str] = {node_id}
        frontier = {node_id}
        selected_edges: List[Dict[str, Any]] = []
        for _ in range(depth):
            following = set()
            for edge in all_edges:
                if edge["source_node_id"] in frontier or edge["target_node_id"] in frontier:
                    selected_edges.append(edge)
                    following.update({edge["source_node_id"], edge["target_node_id"]})
                    if len(selected_edges) >= max(1, min(limit, 300)):
                        break
            following -= discovered
            discovered.update(following)
            frontier = following
            if not frontier or len(selected_edges) >= max(1, min(limit, 300)):
                break
        nodes = [node for node in self.repo.get_graph_nodes(workspace_id) if node["id"] in discovered]
        return {"nodes": [self._public_node(node) for node in nodes], "edges": [self._public_edge(edge) for edge in selected_edges]}

    def path(self, workspace_id: str, source: str, target: str, max_hops: int = 6) -> Optional[Dict[str, Any]]:
        if not self.repo.get_graph_node(workspace_id, source) or not self.repo.get_graph_node(workspace_id, target):
            return None
        # A shortest route is often a poor explanation: a weak heuristic link
        # should not beat a slightly longer chain of explicit evidence.
        relation_weights = {
            "SUPPORTED_BY": 1.0, "SUPPORTS": 1.0, "CONTRADICTS": 0.98,
            "DEPENDS_ON": 0.9, "PRECEDES": 0.82, "MENTIONS": 0.78,
            "HAS_VALUE": 0.76, "CORRELATED_WITH": 0.62,
        }
        edges = [edge for edge in self.repo.get_graph_edges(workspace_id)
                 if edge["confidence"] >= 0.5 and edge["relation_type"] in relation_weights]
        adjacency: Dict[str, List[Dict[str, Any]]] = {}
        for edge in edges:
            adjacency.setdefault(edge["source_node_id"], []).append(edge)
            adjacency.setdefault(edge["target_node_id"], []).append(edge)
        # Dijkstra over -log(edge quality) finds the strongest cumulative
        # explanation. The hop cap keeps the returned path understandable.
        queue = [(0.0, 0, 0, source, [], {source})]
        best_cost: Dict[tuple[str, int], float] = {(source, 0): 0.0}
        while queue:
            cost, hops_count, _tie, current, hops, seen = heapq.heappop(queue)
            if current == target:
                return {"source": source, "target": target, "hops": [self._public_edge(edge) for edge in hops],
                        "path_confidence": round(math.exp(-cost) if hops else 1.0, 3),
                        "explanation": f"Best evidence route found through {len(hops)} relationship(s), ranked by source strength and relation reliability."}
            if hops_count >= max_hops:
                continue
            for edge in adjacency.get(current, []):
                nxt = edge["target_node_id"] if edge["source_node_id"] == current else edge["source_node_id"]
                if nxt in seen:
                    continue
                quality = max(0.01, min(1.0, float(edge["confidence"]) * relation_weights[edge["relation_type"]]))
                next_cost = cost - math.log(quality)
                state = (nxt, hops_count + 1)
                if next_cost >= best_cost.get(state, float("inf")):
                    continue
                best_cost[state] = next_cost
                explicit_tie = 0 if edge.get("evidence_document_id") else 1
                heapq.heappush(queue, (next_cost, hops_count + 1, explicit_tie, nxt, hops + [edge], seen | {nxt}))
        return {"source": source, "target": target, "hops": [], "explanation": "No evidence-backed path was found in this workspace."}

    @staticmethod
    def _public_node(node: Dict[str, Any]) -> Dict[str, Any]:
        metadata = node.get("metadata", {})
        return {"id": node["id"], "type": node["node_type"], "label": node["label"],
                "reference_type": node["reference_type"], "reference_id": node["reference_id"],
                "status": metadata.get("status"), "confidence": metadata.get("confidence"), "metadata": metadata}

    @staticmethod
    def _public_edge(edge: Dict[str, Any]) -> Dict[str, Any]:
        return {"id": edge["id"], "source": edge["source_node_id"], "target": edge["target_node_id"],
                "relation": edge["relation_type"], "confidence": edge["confidence"],
                "explanation": edge.get("explanation", ""), "provenance": {
                    "method": edge.get("provenance_type", "HEURISTIC"), "document_id": edge.get("evidence_document_id"),
                    "chunk_id": edge.get("evidence_chunk_id"), "metadata": edge.get("metadata", {}),
                }}
