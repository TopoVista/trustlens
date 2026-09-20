"""Regression coverage for the evidence-backed intelligence graph projection."""
import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.api.auth import AuthUser, get_current_user, get_current_user_context
from app.knowledge.db import ensure_schema
from app.knowledge.graph_builder import GraphBuilder
from app.knowledge.graph_queries import GraphQueries
from app.knowledge.repository import KnowledgeRepository
from app.main import app
from app.specialists.numeric_verifier import verify_numeric_claim
from app.specialists.relationship_agent import RelationshipAgent
from app.specialists.temporal_verifier import verify_temporal_claim


def _repo(tmp_path):
    db_path = tmp_path / "graph.db"
    ensure_schema(str(db_path))
    return KnowledgeRepository(str(db_path))


def _seed(repo, owner="graph_user"):
    workspace = repo.create_workspace("Evidence", owner_user_id=owner)
    doc = repo.add_document(workspace["id"], "Annual report", "annual.txt", "text", "OpenAI depends on GPU capacity.", "HIGH")
    chunk = {"id": f"chk_{doc}", "workspace_id": workspace["id"], "document_id": doc, "chunk_index": 0,
             "text": "OpenAI depends on GPU capacity. Revenue rose from $100M to $118M.", "location_info": "Section 1"}
    repo.add_chunks([chunk])
    claim = repo.add_claim(workspace["id"], "OpenAI depends on GPU capacity.", doc)
    repo.add_evidence(workspace["id"], claim, doc, chunk["text"], "Section 1", "SUPPORTS", 0.9, chunk_id=chunk["id"])
    repo.add_entity(workspace["id"], "OpenAI", "Organization", ["openai"])
    repo.add_entity(workspace["id"], "GPU Capacity", "Concept", ["gpu capacity"])
    RelationshipAgent(repo).enrich_document(workspace["id"], doc)
    GraphBuilder(repo).rebuild_workspace(workspace["id"])
    return workspace, doc


def test_graph_projection_persists_provenance_and_relationships(tmp_path):
    repo = _repo(tmp_path)
    workspace, _doc = _seed(repo)

    graph = GraphQueries(repo).graph(workspace["id"], min_confidence=0.5)

    assert any(node["type"] == "CLAIM" for node in graph["nodes"])
    assert any(node["type"] == "EVIDENCE" for node in graph["nodes"])
    assert any(edge["relation"] == "SUPPORTED_BY" for edge in graph["edges"])
    assert any(edge["relation"] == "DEPENDS_ON" for edge in graph["edges"])
    supported = next(edge for edge in graph["edges"] if edge["relation"] == "SUPPORTED_BY")
    assert supported["provenance"]["method"] == "NLI"
    assert supported["provenance"]["document_id"]


def test_graph_queries_are_workspace_scoped(tmp_path):
    repo = _repo(tmp_path)
    first, _ = _seed(repo, "owner_a")
    second, _ = _seed(repo, "owner_b")

    first_nodes = GraphQueries(repo).graph(first["id"])["nodes"]
    second_nodes = GraphQueries(repo).graph(second["id"])["nodes"]

    assert first_nodes and second_nodes
    assert {node["id"] for node in first_nodes}.isdisjoint({node["id"] for node in second_nodes})


def test_graph_node_neighbor_path_and_endpoint_enforce_owner(tmp_path):
    repo = _repo(tmp_path)
    workspace, _ = _seed(repo)
    graph = GraphQueries(repo).graph(workspace["id"])
    claim = next(node for node in graph["nodes"] if node["type"] == "CLAIM")
    evidence = next(node for node in graph["nodes"] if node["type"] == "EVIDENCE")
    assert GraphQueries(repo).neighbors(workspace["id"], claim["id"], depth=2)["nodes"]
    assert GraphQueries(repo).path(workspace["id"], claim["id"], evidence["id"])["hops"]

    class Context:
        def __init__(self):
            self.repo = repo

    app.dependency_overrides[get_current_user] = lambda: AuthUser("graph_user", is_authenticated=True)
    app.dependency_overrides[get_current_user_context] = lambda: Context()
    try:
        response = TestClient(app).get(f"/api/workspaces/{workspace['id']}/graph")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["stats"]["nodes"] > 0


def test_numeric_and_temporal_validation_keep_updates_distinct_from_conflicts():
    assert verify_numeric_claim("Revenue grew 18%.", "Revenue rose from $100M to $118M.")["status"] == "NUMERICALLY_VERIFIED"
    assert verify_numeric_claim("Revenue grew 20%.", "Revenue rose from $100M to $118M.")["status"] == "NUMERIC_CONFLICT"
    assert verify_temporal_claim("Launch is June 12.", "Launch was rescheduled to June 19.")["status"] == "UPDATED_BY"


def test_contradictory_evidence_can_project_an_evidence_backed_claim_edge(tmp_path):
    repo = _repo(tmp_path)
    workspace = repo.create_workspace("Dates", owner_user_id="date_user")
    first = repo.add_document(workspace["id"], "Plan", "plan.txt", "text", "Launch is June 12.", "MEDIUM")
    second = repo.add_document(workspace["id"], "Revision", "revision.txt", "text", "Launch is June 19.", "HIGH")
    first_claim = repo.add_claim(workspace["id"], "Launch is June 12.", first)
    second_claim = repo.add_claim(workspace["id"], "Launch is June 19.", second)
    repo.add_evidence(workspace["id"], first_claim, second, "Launch is June 19.", "Section 1", "CONTRADICTS", 0.92)
    GraphBuilder(repo).rebuild_workspace(workspace["id"])
    graph = GraphQueries(repo).graph(workspace["id"], mode="contradictions", min_confidence=0.5)
    assert any(edge["relation"] == "CONTRADICTS" and edge["provenance"]["method"] == "NLI" for edge in graph["edges"])


def test_dataset_variables_and_computed_correlation_enter_graph(tmp_path):
    repo = _repo(tmp_path)
    workspace = repo.create_workspace("Data", owner_user_id="data_user")
    document = repo.add_document(workspace["id"], "Metrics", "metrics.csv", "csv", "Spend,Revenue\n1,2\n2,4\n3,6", "HIGH")
    repo.add_dataset_profile(
        workspace["id"], document, 3, 2, ["Spend", "Revenue"],
        {"Spend": {"type": "Numeric", "stats": {"mean": 2}}, "Revenue": {"type": "Numeric", "stats": {"mean": 4}}},
        [],
    )
    profile = repo.get_dataset_profiles(workspace["id"])[0]
    with repo._get_conn() as conn:
        conn.execute("UPDATE dataset_profiles SET profile_json = ? WHERE id = ?", (
            '{"Spend":{"type":"Numeric","stats":{"mean":2}},"Revenue":{"type":"Numeric","stats":{"mean":4}},"__correlations__":[{"column_a":"Spend","column_b":"Revenue","coefficient":1.0,"sample_size":3}]}', profile["id"],
        ))
    GraphBuilder(repo).rebuild_workspace(workspace["id"])
    graph = GraphQueries(repo).graph(workspace["id"], mode="data", min_confidence=0)
    assert {node["type"] for node in graph["nodes"]} >= {"DATASET", "VARIABLE", "VALUE"}
    assert any(edge["relation"] == "CORRELATED_WITH" and edge["provenance"]["method"] == "STRUCTURED_DATA" for edge in graph["edges"])
