"""Lightweight dataset profiler using only stdlib + numpy.

Supports CSV, JSON (array of objects), Parquet, and Excel (.xlsx).
Produces structured DatasetProfile results without pandas/sklearn.

Memory-safe: reads data in bounded fashion and avoids keeping full copies.
"""
import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

from app.data.types import ColumnProfile, DatasetProfile

# --- Format detection and readers -------------------------------------------

_PARQUET_AVAILABLE = False
try:
    import pyarrow.parquet as pq  # type: ignore
    _PARQUET_AVAILABLE = True
except ImportError:
    pass

_EXCEL_AVAILABLE = False
try:
    import openpyxl  # type: ignore
    _EXCEL_AVAILABLE = True
except ImportError:
    pass


def _detect_format(filename: str) -> str:
    ext = Path(filename).suffix.lower().lstrip(".")
    return {"csv": "csv", "tsv": "csv", "json": "json", "parquet": "parquet",
            "xlsx": "excel", "xls": "excel"}.get(ext, "csv")


def _read_csv(path: str) -> Tuple[List[str], List[List[Any]]]:
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        sample = f.read(8192)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters="\t,;|") if sample.strip() else csv.excel
        except csv.Error:
            # Single-column files or ambiguous content: fall back to standard CSV.
            dialect = csv.excel
        reader = csv.reader(f, dialect)
        try:
            headers = next(reader)
        except StopIteration:
            return [], []
        rows = [row for reader_row in reader for row in [reader_row]]
    return headers, rows


def _read_json(path: str) -> Tuple[List[str], List[List[Any]]]:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        return [], []
    headers = list(data[0].keys()) if isinstance(data[0], dict) else []
    rows = [[row.get(h) for h in headers] for row in data if isinstance(row, dict)]
    return headers, rows


def _read_parquet(path: str) -> Tuple[List[str], List[List[Any]]]:
    if not _PARQUET_AVAILABLE:
        raise ImportError("pyarrow required for Parquet. Install requirements-analytics.txt")
    table = pq.read_table(path)
    headers = table.column_names
    rows = [list(row) for row in table.to_pylist()]
    return headers, rows


def _read_excel(path: str) -> Tuple[List[str], List[List[Any]]]:
    if not _EXCEL_AVAILABLE:
        raise ImportError("openpyxl required for Excel. Install requirements-analytics.txt")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)
    headers = [str(c) if c is not None else f"col_{i}" for i, c in enumerate(next(rows_iter))]
    rows = [list(r) for r in rows_iter]
    wb.close()
    return headers, rows


_READERS = {"csv": _read_csv, "json": _read_json, "parquet": _read_parquet, "excel": _read_excel}


def read_dataset(filename: str, path: str) -> Tuple[List[str], List[List[Any]]]:
    fmt = _detect_format(filename)
    return _READERS[fmt](path)


# --- Column type inference --------------------------------------------------

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}|^\d{2}/\d{2}/\d{4}")


def _infer_column_type(values: List[Any]) -> str:
    non_null = [v for v in values if v is not None and str(v).strip() != ""]
    if not non_null:
        return "empty"
    numeric = 0
    date = 0
    for v in non_null[:200]:
        s = str(v).strip()
        try:
            float(s.replace(",", ""))
            numeric += 1
            continue
        except (ValueError, TypeError):
            pass
        if _DATE_RE.match(s):
            date += 1
    ratio = numeric / len(non_null)
    if ratio > 0.85:
        return "numeric"
    if date / len(non_null) > 0.85:
        return "datetime"
    return "categorical"


def _profile_column(name: str, values: List[Any], row_count: int) -> ColumnProfile:
    null_count = sum(1 for v in values if v is None or str(v).strip() == "")
    non_null = [str(v) for v in values if v is not None and str(v).strip() != ""]
    unique_count = len(set(non_null))
    sample_values = non_null[:5]
    dtype = _infer_column_type(values)

    stats: Dict[str, Any] = {}
    if dtype == "numeric":
        nums = _to_float(values)
        if nums:
            arr = np.array(nums, dtype=np.float64)
            stats = {
                "min": float(np.min(arr)), "max": float(np.max(arr)),
                "mean": float(np.mean(arr)), "median": float(np.median(arr)),
                "std": float(np.std(arr)),
                "q25": float(np.percentile(arr, 25)),
                "q75": float(np.percentile(arr, 75)),
            }
    elif dtype == "categorical":
        freq: Dict[str, int] = {}
        for v in non_null:
            freq[v] = freq.get(v, 0) + 1
        top = sorted(freq.items(), key=lambda x: -x[1])[:10]
        stats = {"top_values": [{"value": k, "count": v} for k, v in top],
                 "unique_count": unique_count}
    elif dtype == "datetime":
        stats = {"sample_values": sample_values[:3]}

    return ColumnProfile(
        name=name, dtype=dtype,
        null_count=null_count,
        null_percentage=round(null_count / max(row_count, 1) * 100, 2),
        unique_count=unique_count,
        unique_percentage=round(unique_count / max(row_count, 1) * 100, 2),
        sample_values=sample_values, stats=stats,
    )


def profile_dataset(filename: str, path: str, dataset_id: str = "") -> DatasetProfile:
    """Profile a dataset file and return a structured DatasetProfile."""
    headers, rows = read_dataset(filename, path)
    row_count = len(rows)
    column_count = len(headers)

    columns: List[ColumnProfile] = []
    numeric_columns, categorical_columns, datetime_columns = [], [], []
    missing_columns, constant_columns = [], []
    likely_id_columns, potential_target_columns = [], []

    for i, name in enumerate(headers):
        col_values = [row[i] if i < len(row) else None for row in rows]
        cp = _profile_column(name, col_values, row_count)
        columns.append(cp)
        if cp.dtype == "numeric":
            numeric_columns.append(name)
        elif cp.dtype == "datetime":
            datetime_columns.append(name)
        else:
            categorical_columns.append(name)
        if cp.null_count > 0:
            missing_columns.append(name)
        if cp.unique_count <= 1:
            constant_columns.append(name)
        if cp.unique_count == row_count and row_count > 1:
            # String-like columns with all-unique values are classic IDs
            # ("user_001", "A1F3"). Numeric columns only qualify when they are
            # integer-like AND sequential (row-index style); continuous
            # measurements (revenue, customers) must not be flagged.
            if cp.dtype == "categorical":
                likely_id_columns.append(name)
            elif cp.dtype == "numeric" and row_count > 2:
                nums = _to_float(col_values)
                if nums and all(v == int(v) for v in nums):
                    ordered = sorted(nums)
                    if ordered[0] in (0, 1) and all(
                        ordered[j + 1] - ordered[j] == 1
                        for j in range(len(ordered) - 1)
                    ):
                        likely_id_columns.append(name)

    for name in numeric_columns:
        cp = next(c for c in columns if c.name == name)
        if 2 < cp.unique_count < max(50, row_count * 0.3):
            potential_target_columns.append(name)

    mem_bytes = row_count * column_count * 20
    memory_estimate_mb = round(mem_bytes / (1024 * 1024), 2)

    duplicate_count = 0
    if rows:
        seen = set()
        for row in rows:
            key = tuple(str(c) for c in row)
            if key in seen:
                duplicate_count += 1
            else:
                seen.add(key)

    data_quality = {
        "completeness_pct": round(
            (1 - sum(c.null_count for c in columns) / max(row_count * column_count, 1)) * 100, 2),
        "duplicate_rate_pct": round(duplicate_count / max(row_count, 1) * 100, 2),
    }

    return DatasetProfile(
        dataset_id=dataset_id, source_type=_detect_format(filename),
        filename=filename, row_count=row_count, column_count=column_count,
        columns=columns, numeric_columns=numeric_columns,
        categorical_columns=categorical_columns, datetime_columns=datetime_columns,
        missing_columns=missing_columns, duplicate_count=duplicate_count,
        constant_columns=constant_columns, likely_id_columns=likely_id_columns,
        potential_target_columns=potential_target_columns,
        memory_estimate_mb=memory_estimate_mb, data_quality=data_quality,
    )


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