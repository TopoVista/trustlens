"""Regression coverage for the lightweight Phase 3-7 additions."""
import sys
from pathlib import Path
from fastapi.testclient import TestClient

backend = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend))

from app.analytics.query import QueryPlan, QueryPlanError, execute_plan, interpret_question
from app.analytics.advanced import forecast
from app.agents.coordinator import Coordinator


def test_nl_average_and_safe_plan_execution():
    headers, rows = ["region", "revenue"], [["East", "10"], ["West", "30"]]
    plan = interpret_question("What is average revenue?", headers, rows)
    assert plan and execute_plan(plan, headers, rows)["rows"] == [{"mean_revenue": 20.0}]


def test_query_rejects_injection_as_column_name():
    plan = QueryPlan.from_dict({"metrics":[{"column":"__import__('os')", "aggregation":"sum"}]})
    try: execute_plan(plan, ["revenue"], [["1"]])
    except QueryPlanError: pass
    else: assert False, "invalid schema reference must not run"


def test_forecast_and_coordinator_are_opt_in_and_bounded():
    assert forecast([1, 2], periods=2)["status"] == "forecast_not_applicable"
    assert forecast([1, 2, 3], periods=2)["status"] == "ok"
    assert [x["specialist"] for x in Coordinator().run_timeline("forecast sales")] == ["profiling", "forecasting"]


def test_dataset_api_does_not_disclose_another_users_upload():
    from app.main import app
    client = TestClient(app)
    owner = {"x-user-id": "dataset-owner"}
    other = {"x-user-id": "dataset-other"}
    upload = client.post("/datasets/upload?filename=x.csv", content=b"amount\n1\n2\n", headers=owner)
    dataset_id = upload.json()["dataset_id"]
    try:
        assert client.get(f"/datasets/{dataset_id}", headers=other).status_code == 404
    finally:
        assert client.delete(f"/datasets/{dataset_id}", headers=owner).status_code == 200
