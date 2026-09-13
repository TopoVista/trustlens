"""Regression coverage for the workspace query Server-Sent Event contract."""
import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import app.api.auth as auth_mod
from app.api.auth import get_current_user_context
from app.main import app


class _Repo:
    def get_workspace(self, workspace_id):
        return {"id": workspace_id, "owner_user_id": "stream_user"}


class _Planner:
    async def execute_plan(self, _workspace_id, query, on_progress=None):
        await on_progress("Searching the workspace for relevant source passages.")
        await on_progress("Synthesizing the answer while preserving evidence and uncertainty.")
        return {
            "query": query,
            "intent": "FACTUAL_QUERY",
            "answer": "Streamed answer.",
            "confidence": 0.8,
            "claims": [],
            "evidence": [],
            "contradictions": [],
            "assumptions": [],
            "unknowns": [],
            "related_knowledge": {},
            "plan_trace": [],
            "latency_ms": 1.0,
        }


class _Context:
    repo = _Repo()
    planner = _Planner()


def test_workspace_query_stream_emits_status_lines_then_result(monkeypatch):
    monkeypatch.setattr(auth_mod, "AUTH_MODE", "dev")
    app.dependency_overrides[get_current_user_context] = lambda: _Context()
    try:
        response = TestClient(app).post(
            "/api/workspaces/workspace_1/query/stream",
            headers={"x-user-id": "stream_user"},
            json={"query": "What does the source say?"},
        )
    finally:
        app.dependency_overrides.pop(get_current_user_context, None)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text.count("event: status") == 2
    assert "Searching the workspace for relevant source passages." in response.text
    assert "event: result" in response.text
    assert '"answer":"Streamed answer."' in response.text
