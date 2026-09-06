"""Deterministic dataset analytics engine for TrustLens.

Modules:
    profiling — dataset readers + profiler (CSV/JSON/Parquet/Excel)
    eda       — descriptive statistics, correlations, outlier detection
    insights  — deterministic insight detection
    charts    — JSON chart-spec generation

All heavy dependencies (pandas/sklearn) are intentionally absent; the engine
uses only the Python standard library plus numpy so the Render Free runtime
stays lightweight.
"""
from app.data.types import ChartSpec, ColumnProfile, DatasetProfile, Insight

__all__ = ["ChartSpec", "ColumnProfile", "DatasetProfile", "Insight"]

