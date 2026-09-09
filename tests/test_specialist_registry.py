"""Registry and dataset-specialist regression tests."""
import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.planner.registry import AgentRegistry


def test_registry_contains_dataset_specialists_and_is_lazy():
    registry = AgentRegistry()
    assert registry._specialists == {}
    assert {"data_profiler", "eda_analyst", "insight_analyst", "visualization_analyst", "anomaly_analyst"} <= set(registry._factories)
    specialist = registry.get("data_profiler")
    assert specialist.name == "Data Profiler"
    assert set(registry._specialists) == {"data_profiler"}
    assert registry.find_by_capability("chart_selection")[0].name == "Visualization Analyst"


def test_dataset_specialists_return_structured_results(tmp_path):
    path = tmp_path / "sales.csv"
    path.write_text("region,revenue\nEast,10\nWest,30\nEast,20\n", encoding="utf-8")
    context = {"filename": "sales.csv", "path": str(path), "dataset_id": "test"}
    registry = AgentRegistry()
    profile = asyncio.run(registry.get("data_profiler").analyze("ws", context))
    eda = asyncio.run(registry.get("eda_analyst").analyze("ws", context))
    charts = asyncio.run(registry.get("visualization_analyst").analyze("ws", context))
    assert profile["row_count"] == 3
    assert eda["statistics"]["revenue"]["mean"] == 20.0
    assert charts["charts"]
