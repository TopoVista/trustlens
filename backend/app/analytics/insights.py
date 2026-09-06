"""Deterministic insight detector.

Analyzes a DatasetProfile + raw data to produce structured Insights.
The LLM later turns these into prose — the numbers always come from here.
"""
from typing import Any, Dict, List, Optional

import numpy as np

from app.data.types import DatasetProfile, Insight


def _to_float(values: List[Any]) -> List[float]:
    out = []
    for v in values:
        if v is None or str(v).strip() == "":
            continue
        try:
            out.append(float(str(v).replace(",", "")))
        except (ValueError, TypeError):
            pass
    return out


def detect_insights(profile: DatasetProfile, headers: List[str],
                    rows: List[List[Any]]) -> List[Insight]:
    """Generate deterministic insights from a profiled dataset."""
    insights: List[Insight] = []
    col_idx = {h: i for i, h in enumerate(headers)}
    row_count = profile.row_count

    # Missingness
    for col in profile.columns:
        if col.null_percentage > 50:
            insights.append(Insight(
                type="missingness", severity="high",
                title=f"Column '{col.name}' is {col.null_percentage}% missing",
                columns=[col.name],
                evidence={"null_count": col.null_count, "null_pct": col.null_percentage},
            ))
        elif col.null_percentage > 10:
            insights.append(Insight(
                type="missingness", severity="medium",
                title=f"Column '{col.name}' has {col.null_percentage}% missing values",
                columns=[col.name],
                evidence={"null_count": col.null_count, "null_pct": col.null_percentage},
            ))

    # Duplicates
    if profile.duplicate_count > 0:
        rate = round(profile.duplicate_count / max(row_count, 1) * 100, 1)
        severity = "high" if rate > 20 else "medium" if rate > 5 else "low"
        insights.append(Insight(
            type="duplicates", severity=severity,
            title=f"{profile.duplicate_count} duplicate rows detected ({rate}%)",
            evidence={"duplicate_count": profile.duplicate_count, "rate_pct": rate},
        ))

    # Constant columns
    for name in profile.constant_columns:
        insights.append(Insight(
            type="constant", severity="low",
            title=f"Column '{name}' has a constant value",
            columns=[name], evidence={},
        ))

    # Numeric outliers
    for name in profile.numeric_columns:
        idx = col_idx.get(name)
        if idx is None:
            continue
        values = [row[idx] if idx < len(row) else None for row in rows]
        nums = _to_float(values)
        if len(nums) < 4:
            continue
        arr = np.array(nums, dtype=np.float64)
        q25, q75 = np.percentile(arr, 25), np.percentile(arr, 75)
        iqr = q75 - q25
        if iqr == 0:
            continue
        outliers = int(np.sum((arr < q25 - 1.5 * iqr) | (arr > q75 + 1.5 * iqr)))
        if outliers > 0:
            pct = round(outliers / len(nums) * 100, 1)
            insights.append(Insight(
                type="outliers", severity="high" if pct > 10 else "medium",
                title=f"Column '{name}' has {outliers} outliers ({pct}%)",
                columns=[name],
                evidence={"outlier_count": outliers, "pct": pct,
                          "q25": round(float(q25), 4), "q75": round(float(q75), 4)},
            ))

    # Category dominance
    for name in profile.categorical_columns:
        idx = col_idx.get(name)
        if idx is None:
            continue
        values = [str(row[idx]) for row in rows if idx < len(row) and row[idx] is not None]
        if not values:
            continue
        freq: Dict[str, int] = {}
        for v in values:
            freq[v] = freq.get(v, 0) + 1
        top_val, top_count = max(freq.items(), key=lambda x: x[1])
        dominance = round(top_count / len(values) * 100, 1)
        if dominance > 70:
            insights.append(Insight(
                type="category_dominance", severity="medium",
                title=f"Category '{top_val}' dominates '{name}' ({dominance}%)",
                columns=[name],
                evidence={"top_category": top_val, "dominance_pct": dominance,
                          "count": top_count},
            ))

    # Strong correlations
    if len(profile.numeric_columns) >= 2:
        from app.analytics.eda import compute_correlations
        corrs = compute_correlations(headers, rows, profile.numeric_columns[:20])
        for c in corrs:
            if c["strength"] == "strong":
                insights.append(Insight(
                    type="correlation", severity="medium",
                    title=f"Strong {c['direction']} correlation between '{c['column_a']}' and '{c['column_b']}' (r={c['correlation']})",
                    columns=[c["column_a"], c["column_b"]],
                    evidence=c,
                ))

    return sorted(insights, key=lambda i: {"high": 0, "medium": 1, "low": 2}.get(i.severity, 3))