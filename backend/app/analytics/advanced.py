"""Opt-in, dependency-free advanced analytics primitives."""
from __future__ import annotations
from collections import defaultdict
from typing import Any, Dict, List, Optional
import math

from app.analytics.profiling import _to_float


def detect_anomalies(values: List[Any], method: str = "iqr") -> Dict[str, Any]:
    nums = _to_float(values)
    if len(nums) < 4: return {"status": "not_applicable", "indices": [], "method": method}
    ordered = sorted(nums)
    q1, q3 = ordered[len(ordered)//4], ordered[(len(ordered)*3)//4]
    iqr = q3 - q1
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    indices = [i for i, v in enumerate(nums) if v < low or v > high]
    return {"status":"ok", "method":"iqr", "indices":indices, "count":len(indices), "lower_bound":low, "upper_bound":high}


def forecast(values: List[Any], periods: int = 3, method: str = "moving_average") -> Dict[str, Any]:
    nums = _to_float(values)
    if len(nums) < 3 or not 1 <= periods <= 100:
        return {"status":"forecast_not_applicable", "reason":"At least three observations and a bounded horizon are required."}
    window = min(3, len(nums))
    prediction = sum(nums[-window:]) / window
    # A simple uncertainty estimate communicates the limitation without a heavy model.
    variance = sum((x - prediction) ** 2 for x in nums[-window:]) / window
    return {"status":"ok", "method":method, "forecast_values":[round(prediction, 10)] * periods, "historical_baseline":round(prediction, 10), "uncertainty":round(math.sqrt(variance), 10), "limitations":"Moving-average baseline; it does not model seasonality or causal effects."}


def dashboard_spec(profile: Dict[str, Any], insights: List[Dict[str, Any]], charts: List[Dict[str, Any]], title: Optional[str] = None) -> Dict[str, Any]:
    numeric = profile.get("numeric_columns", [])
    kpis = [{"label":"Rows", "value":profile.get("row_count", 0)}, {"label":"Columns", "value":profile.get("column_count", 0)}]
    return {"title":title or f"{profile.get('filename', 'Dataset')} Overview", "description":"Deterministically generated dataset overview.", "kpis":kpis, "charts":charts[:8], "filters":[{"column": c, "type":"categorical"} for c in profile.get("categorical_columns", [])[:5]], "insights":insights[:10], "metadata":{"numeric_columns":numeric}}
