"""Deterministic EDA engine — calculates facts, not narratives.

Produces structured analysis results using only stdlib + numpy.
"""
from typing import Any, Dict, List, Tuple

import numpy as np

from app.data.types import ColumnProfile


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


def compute_statistics(values: List[Any]) -> Dict[str, Any]:
    """Compute descriptive statistics for a numeric column."""
    nums = _to_float(values)
    if not nums:
        return {}
    arr = np.array(nums, dtype=np.float64)
    return {
        "count": len(nums), "min": float(np.min(arr)), "max": float(np.max(arr)),
        "mean": round(float(np.mean(arr)), 4), "median": round(float(np.median(arr)), 4),
        "std": round(float(np.std(arr)), 4),
        "q25": round(float(np.percentile(arr, 25)), 4),
        "q75": round(float(np.percentile(arr, 75)), 4),
    }


def compute_correlations(headers: List[str], rows: List[List[Any]],
                         numeric_columns: List[str]) -> List[Dict[str, Any]]:
    """Compute Pearson correlations between numeric columns (bounded)."""
    if len(numeric_columns) > 50:
        numeric_columns = numeric_columns[:50]
    col_idx = {h: i for i, h in enumerate(headers)}
    matrices = {}
    for name in numeric_columns:
        idx = col_idx.get(name)
        if idx is None:
            continue
        matrices[name] = _to_float([row[idx] if idx < len(row) else None for row in rows])

    results = []
    names = list(matrices.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = matrices[names[i]], matrices[names[j]]
            paired = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
            if len(paired) < 3:
                continue
            x = np.array([p[0] for p in paired])
            y = np.array([p[1] for p in paired])
            if np.std(x) == 0 or np.std(y) == 0:
                continue
            corr = float(np.corrcoef(x, y)[0, 1])
            if abs(corr) >= 0.5:
                results.append({
                    "column_a": names[i], "column_b": names[j],
                    "correlation": round(corr, 4),
                    "strength": "strong" if abs(corr) >= 0.7 else "moderate",
                    "direction": "positive" if corr > 0 else "negative",
                })
    return sorted(results, key=lambda r: -abs(r["correlation"]))[:20]


def detect_outliers_iqr(values: List[Any]) -> Dict[str, Any]:
    """Detect outliers using the IQR method."""
    nums = _to_float(values)
    if len(nums) < 4:
        return {"count": 0, "indices": [], "threshold_low": None, "threshold_high": None}
    arr = np.array(nums, dtype=np.float64)
    q25, q75 = np.percentile(arr, 25), np.percentile(arr, 75)
    iqr = q75 - q25
    low, high = q25 - 1.5 * iqr, q75 + 1.5 * iqr
    indices = [i for i, v in enumerate(nums) if v < low or v > high]
    return {
        "count": len(indices), "indices": indices[:50],
        "threshold_low": round(float(low), 4), "threshold_high": round(float(high), 4),
    }


def detect_outliers_zscore(values: List[Any], threshold: float = 3.0) -> Dict[str, Any]:
    """Detect outliers using z-score."""
    nums = _to_float(values)
    if len(nums) < 4:
        return {"count": 0, "indices": []}
    arr = np.array(nums, dtype=np.float64)
    mean, std = np.mean(arr), np.std(arr)
    if std == 0:
        return {"count": 0, "indices": []}
    indices = [i for i, v in enumerate(nums) if abs((v - mean) / std) > threshold]
    return {"count": len(indices), "indices": indices[:50]}