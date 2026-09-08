"""Safe, deterministic tabular query planning and execution.

This module intentionally has no code-evaluation path: plans are data and the
executor only implements the small allow-list below.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Any, Dict, List, Optional

from app.analytics.profiling import _infer_column_type, read_dataset

ALLOWED_AGGREGATIONS = {"count", "sum", "mean", "median", "min", "max"}
MAX_LIMIT = 1000


class QueryPlanError(ValueError):
    pass


@dataclass
class Metric:
    column: Optional[str] = None
    aggregation: str = "count"


@dataclass
class QueryPlan:
    operation: str = "aggregate"
    dimensions: List[str] = field(default_factory=list)
    metrics: List[Metric] = field(default_factory=list)
    filters: List[Dict[str, Any]] = field(default_factory=list)
    sort: Optional[Dict[str, str]] = None
    limit: int = 100
    date_granularity: Optional[str] = None

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "QueryPlan":
        metrics = [Metric(**m) for m in value.get("metrics", [])]
        return cls(operation=value.get("operation", "aggregate"), dimensions=list(value.get("dimensions", [])), metrics=metrics, filters=list(value.get("filters", [])), sort=value.get("sort"), limit=value.get("limit", 100), date_granularity=value.get("date_granularity"))

    def to_dict(self) -> Dict[str, Any]:
        return {"operation": self.operation, "dimensions": self.dimensions, "metrics": [m.__dict__ for m in self.metrics], "filters": self.filters, "sort": self.sort, "limit": self.limit, "date_granularity": self.date_granularity}


def validate_plan(plan: QueryPlan, headers: List[str], rows: List[List[Any]]) -> None:
    if plan.operation not in {"aggregate", "group_by", "top_n", "comparison", "percentage_change"}:
        raise QueryPlanError("unsupported operation")
    if not isinstance(plan.limit, int) or not 1 <= plan.limit <= MAX_LIMIT:
        raise QueryPlanError(f"limit must be between 1 and {MAX_LIMIT}")
    types = {h: _infer_column_type([r[i] if i < len(r) else None for r in rows]) for i, h in enumerate(headers)}
    for col in plan.dimensions:
        if col not in headers:
            raise QueryPlanError(f"unknown column: {col}")
    if not plan.metrics:
        plan.metrics = [Metric(None, "count")]
    for metric in plan.metrics:
        if metric.aggregation not in ALLOWED_AGGREGATIONS:
            raise QueryPlanError(f"unsupported aggregation: {metric.aggregation}")
        if metric.aggregation != "count":
            if not metric.column or metric.column not in headers:
                raise QueryPlanError(f"unknown metric column: {metric.column}")
            if types[metric.column] != "numeric":
                raise QueryPlanError(f"{metric.aggregation} requires numeric column: {metric.column}")
    for item in plan.filters:
        if not isinstance(item, dict) or item.get("column") not in headers or item.get("operator", "eq") not in {"eq", "ne", "gt", "gte", "lt", "lte", "contains"}:
            raise QueryPlanError("invalid filter")
    if plan.date_granularity and (not plan.dimensions or types.get(plan.dimensions[0]) != "datetime"):
        raise QueryPlanError("date grouping requires a datetime dimension")


def _number(value: Any) -> Optional[float]:
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _match(value: Any, item: Dict[str, Any]) -> bool:
    expected, op = item.get("value"), item.get("operator", "eq")
    if op == "contains": return str(expected).lower() in str(value).lower()
    left, right = _number(value), _number(expected)
    if left is None or right is None: left, right = str(value), str(expected)
    return {"eq": left == right, "ne": left != right, "gt": left > right, "gte": left >= right, "lt": left < right, "lte": left <= right}[op]


def _aggregate(values: List[Any], aggregation: str) -> Any:
    if aggregation == "count": return len(values)
    nums = [x for v in values if (x := _number(v)) is not None]
    if not nums: return None
    nums.sort()
    if aggregation == "sum": return round(sum(nums), 10)
    if aggregation == "mean": return round(sum(nums) / len(nums), 10)
    if aggregation == "median": return round(nums[len(nums)//2] if len(nums) % 2 else (nums[len(nums)//2-1] + nums[len(nums)//2]) / 2, 10)
    return min(nums) if aggregation == "min" else max(nums)


def execute_plan(plan: QueryPlan, headers: List[str], rows: List[List[Any]]) -> Dict[str, Any]:
    validate_plan(plan, headers, rows)
    indexed = [{h: r[i] if i < len(r) else None for i, h in enumerate(headers)} for r in rows]
    indexed = [r for r in indexed if all(_match(r.get(f["column"]), f) for f in plan.filters)]
    groups: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for row in indexed:
        key = tuple(row.get(d) for d in plan.dimensions) if plan.dimensions else tuple()
        groups[key].append(row)
    result = []
    for key, members in groups.items():
        record = {d: key[i] for i, d in enumerate(plan.dimensions)}
        for m in plan.metrics:
            label = "count" if m.aggregation == "count" and not m.column else f"{m.aggregation}_{m.column}"
            record[label] = _aggregate([None] * len(members) if m.aggregation == "count" else [r.get(m.column or "") for r in members], m.aggregation)
        result.append(record)
    if plan.sort:
        col, reverse = plan.sort.get("column"), plan.sort.get("direction", "asc") == "desc"
        if col not in (result[0] if result else {}): raise QueryPlanError(f"unknown sort column: {col}")
        result.sort(key=lambda x: (x.get(col) is None, x.get(col)), reverse=reverse)
    return {"row_count": len(result), "rows": result[:plan.limit], "filtered_source_rows": len(indexed)}


def interpret_question(question: str, headers: List[str], rows: List[List[Any]]) -> Optional[QueryPlan]:
    """Small analytics-only parser. It deliberately declines ambiguous text."""
    q = question.lower().strip()
    aliases = {h.lower(): h for h in headers}
    def col_after(words: str) -> Optional[str]:
        for name, original in aliases.items():
            if name in words: return original
        return None
    aggregation = next((a for a in ("average", "mean", "median", "total", "sum", "minimum", "min", "maximum", "max", "count") if re.search(rf"\b{a}\b", q)), None)
    agg = {"average":"mean", "total":"sum", "minimum":"min", "maximum":"max"}.get(aggregation or "", aggregation)
    dimensions = []
    if " by " in q:
        dimensions = [col_after(q.split(" by ", 1)[1])]
        dimensions = [d for d in dimensions if d]
    metric_col = col_after(q)
    if "how many" in q or "count" in q: agg, metric_col = "count", None
    if not agg: return None
    if agg != "count" and not metric_col: return None
    return QueryPlan(operation="group_by" if dimensions else "aggregate", dimensions=dimensions, metrics=[Metric(metric_col, agg)], limit=10 if "top" in q or "highest" in q else 100, sort={"column": f"{agg}_{metric_col}" if metric_col else "count", "direction":"desc"} if dimensions and ("top" in q or "highest" in q) else None)


def answer_question(filename: str, path: str, question: str) -> Dict[str, Any]:
    headers, rows = read_dataset(filename, path)
    plan = interpret_question(question, headers, rows)
    if plan is None: return {"status": "unsupported_query", "interpretation": "No deterministic interpretation is available for this question."}
    result = execute_plan(plan, headers, rows)
    return {"status": "ok", "interpretation": "Deterministic analytics-only interpretation", "query_plan": plan.to_dict(), "result": result}
