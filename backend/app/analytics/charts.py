"""Deterministic chart specification engine.

Produces JSON-serializable chart specs from dataset metadata.
Chart selection follows deterministic rules — no LLM code generation.
"""
from typing import Any, Dict, List, Optional

from app.data.types import ChartSpec, DatasetProfile


def _pick_chart_type(x_dtype: str, y_dtype: str) -> Optional[str]:
    if x_dtype == "datetime" and y_dtype == "numeric":
        return "line"
    if x_dtype == "categorical" and y_dtype == "numeric":
        return "bar"
    if x_dtype == "numeric" and y_dtype == "numeric":
        return "scatter"
    if x_dtype == "categorical" and y_dtype in ("categorical", "empty"):
        return "frequency"
    if x_dtype == "numeric" and y_dtype in ("categorical", "empty"):
        return "histogram"
    return None


def suggest_charts(profile: DatasetProfile) -> List[ChartSpec]:
    """Generate suggested chart specs for a profiled dataset."""
    charts: List[ChartSpec] = []
    col_map = {c.name: c for c in profile.columns}

    # Single-column charts first
    for col in profile.columns:
        if col.dtype == "numeric":
            charts.append(ChartSpec(
                type="histogram", title=f"Distribution of {col.name}",
                column=col.name, extra={"bins": 20},
            ))
        elif col.dtype == "categorical" and col.unique_count <= 50:
            charts.append(ChartSpec(
                type="frequency", title=f"Frequency of {col.name}",
                column=col.name, extra={"top_n": 15},
            ))

    # Time series
    datetime_cols = [c for c in profile.columns if c.dtype == "datetime"]
    numeric_cols = [c for c in profile.columns if c.dtype == "numeric"]
    for dt in datetime_cols[:2]:
        for num in numeric_cols[:3]:
            charts.append(ChartSpec(
                type="line", title=f"{num.name} over {dt.name}",
                x=dt.name, y=num.name,
            ))

    # Categorical vs numeric (bar charts)
    cat_cols = [c for c in profile.columns if c.dtype == "categorical" and c.unique_count <= 30]
    for cat in cat_cols[:3]:
        for num in numeric_cols[:2]:
            charts.append(ChartSpec(
                type="bar", title=f"{num.name} by {cat.name}",
                x=cat.name, y=num.name, aggregation="mean",
            ))

    # Scatter pairs (limited)
    if len(numeric_cols) >= 2:
        for i in range(min(3, len(numeric_cols))):
            for j in range(i + 1, min(4, len(numeric_cols))):
                charts.append(ChartSpec(
                    type="scatter", title=f"{numeric_cols[j].name} vs {numeric_cols[i].name}",
                    x=numeric_cols[i].name, y=numeric_cols[j].name,
                ))

    return charts[:20]


def build_chart_data(profile: DatasetProfile, headers: List[List[str]],
                     spec: ChartSpec) -> Dict[str, Any]:
    """Materialize data points for a chart spec from raw rows."""
    # This is a simplified materialization — frontend can enhance
    result = spec.to_dict()
    result["data"] = []
    return result