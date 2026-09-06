"""Specialist wrappers for the TrustLens dataset analytics engine.

Each specialist wraps a deterministic analytics module and exposes the
standard ``BaseSpecialist`` interface so the coordinator can dispatch
to them dynamically. These are in-process reasoning modules, not separate
servers or agents.
"""
from typing import Any, Dict, List

from app.specialists.base import BaseSpecialist


class DataProfiler(BaseSpecialist):
    """Profiles tabular datasets and returns structured metadata."""

    def __init__(self):
        super().__init__(
            name="Data Profiler",
            description="Inspects a dataset and produces row/column counts, "
                        "data types, missing values, duplicates, constant "
                        "columns, and likely ID/target columns.",
            capabilities=["data_profiling", "schema_detection", "data_quality"],
        )

    async def analyze(self, workspace_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        from app.analytics.profiling import profile_dataset

        filename = context.get("filename", "dataset.csv")
        path = context.get("path", "")
        dataset_id = context.get("dataset_id", workspace_id)
        profile = profile_dataset(filename, path, dataset_id)
        return profile.to_dict()


class EDAAnalyst(BaseSpecialist):
    """Runs deterministic exploratory data analysis on tabular data."""

    def __init__(self):
        super().__init__(
            name="EDA Analyst",
            description="Computes descriptive statistics, correlations, "
                        "and outlier candidates for numeric columns.",
            capabilities=["eda", "statistics", "correlations", "outliers"],
        )

    async def analyze(self, workspace_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        from app.analytics.profiling import read_dataset
        from app.analytics.eda import (
            compute_statistics,
            compute_correlations,
            detect_outliers_iqr,
        )

        filename = context.get("filename", "dataset.csv")
        path = context.get("path", "")
        headers, rows = read_dataset(filename, path)

        numeric_cols = []
        col_values: Dict[str, List[Any]] = {}
        for i, name in enumerate(headers):
            vals = [row[i] if i < len(row) else None for row in rows]
            col_values[name] = vals
            sample = [v for v in vals if v is not None and str(v).strip() != ""][:10]
            try:
                [float(str(v).replace(",", "")) for v in sample]
                numeric_cols.append(name)
            except (ValueError, TypeError):
                pass

        stats = {name: compute_statistics(col_values[name]) for name in numeric_cols}
        correlations = compute_correlations(headers, rows, numeric_cols) if len(numeric_cols) >= 2 else []
        outliers = {name: detect_outliers_iqr(col_values[name]) for name in numeric_cols}

        return {
            "row_count": len(rows),
            "column_count": len(headers),
            "numeric_columns": numeric_cols,
            "statistics": stats,
            "correlations": correlations,
            "outliers": outliers,
        }


class InsightAnalyst(BaseSpecialist):
    """Detects deterministic insights from a profiled dataset."""

    def __init__(self):
        super().__init__(
            name="Insight Analyst",
            description="Detects missingness, duplicates, outliers, dominant "
                        "categories, high-cardinality columns, and strong "
                        "correlations.",
            capabilities=["insight_detection", "anomaly_detection", "data_quality"],
        )

    async def analyze(self, workspace_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        from app.analytics.profiling import profile_dataset, read_dataset
        from app.analytics.insights import detect_insights

        filename = context.get("filename", "dataset.csv")
        path = context.get("path", "")
        dataset_id = context.get("dataset_id", workspace_id)
        profile = profile_dataset(filename, path, dataset_id)
        headers, rows = read_dataset(filename, path)
        insights = detect_insights(profile, headers, rows)
        return {
            "insights": [i.to_dict() for i in insights],
            "profile": profile.to_dict(),
        }


class VisualizationAnalyst(BaseSpecialist):
    """Produces deterministic chart specifications for a dataset."""

    def __init__(self):
        super().__init__(
            name="Visualization Analyst",
            description="Recommends chart types (line, bar, histogram, "
                        "scatter, frequency) based on column types.",
            capabilities=["visualization", "chart_selection"],
        )

    async def analyze(self, workspace_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        from app.analytics.profiling import profile_dataset
        from app.analytics.charts import suggest_charts

        filename = context.get("filename", "dataset.csv")
        path = context.get("path", "")
        dataset_id = context.get("dataset_id", workspace_id)
        profile = profile_dataset(filename, path, dataset_id)
        charts = suggest_charts(profile)
        return {"charts": [c.to_dict() for c in charts]}


class AnomalyAnalyst(BaseSpecialist):
    """Detects anomalies using lightweight statistical methods."""

    def __init__(self):
        super().__init__(
            name="Anomaly Analyst",
            description="Flags numeric outliers via IQR and detects "
                        "suspicious columns.",
            capabilities=["anomaly_detection", "outlier_detection"],
        )

    async def analyze(self, workspace_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        from app.analytics.profiling import read_dataset
        from app.analytics.eda import detect_outliers_iqr

        filename = context.get("filename", "dataset.csv")
        path = context.get("path", "")
        headers, rows = read_dataset(filename, path)

        results: Dict[str, Any] = {}
        for i, name in enumerate(headers):
            vals = [row[i] if i < len(row) else None for row in rows]
            nums = []
            for v in vals:
                if v is None or str(v).strip() == "":
                    continue
                try:
                    nums.append(float(str(v).replace(",", "")))
                except (ValueError, TypeError):
                    break
            else:
                if nums:
                    results[name] = detect_outliers_iqr(vals)
        return {"anomalies": results}

