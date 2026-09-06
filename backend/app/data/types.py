"""Typed result models for the TrustLens dataset analytics engine.

Lightweight Pydantic-free typed structures describing dataset profiles,
column profiles, data quality, insights, and chart specifications.

Kept dependency-free (plain classes + typing) so they can be imported
anywhere without pulling in heavy packages.
"""
from typing import Any, Dict, List, Optional


class ColumnProfile:
    """Profile for a single dataset column."""

    def __init__(
        self,
        name: str,
        dtype: str,
        null_count: int = 0,
        null_percentage: float = 0.0,
        unique_count: int = 0,
        unique_percentage: float = 0.0,
        sample_values: Optional[List[str]] = None,
        stats: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.dtype = dtype
        self.null_count = null_count
        self.null_percentage = null_percentage
        self.unique_count = unique_count
        self.unique_percentage = unique_percentage
        self.sample_values = sample_values or []
        self.stats = stats or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "dtype": self.dtype,
            "null_count": self.null_count,
            "null_percentage": self.null_percentage,
            "unique_count": self.unique_count,
            "unique_percentage": self.unique_percentage,
            "sample_values": self.sample_values,
            "stats": self.stats,
        }


class DatasetProfile:
    """Comprehensive profile of a tabular dataset."""

    def __init__(
        self,
        dataset_id: str,
        source_type: str,
        filename: str,
        row_count: int,
        column_count: int,
        columns: List[ColumnProfile],
        numeric_columns: List[str],
        categorical_columns: List[str],
        datetime_columns: List[str],
        missing_columns: List[str],
        duplicate_count: int,
        constant_columns: List[str],
        likely_id_columns: List[str],
        potential_target_columns: List[str],
        memory_estimate_mb: float,
        data_quality: Optional[Dict[str, Any]] = None,
    ):
        self.dataset_id = dataset_id
        self.source_type = source_type
        self.filename = filename
        self.row_count = row_count
        self.column_count = column_count
        self.columns = columns
        self.numeric_columns = numeric_columns
        self.categorical_columns = categorical_columns
        self.datetime_columns = datetime_columns
        self.missing_columns = missing_columns
        self.duplicate_count = duplicate_count
        self.constant_columns = constant_columns
        self.likely_id_columns = likely_id_columns
        self.potential_target_columns = potential_target_columns
        self.memory_estimate_mb = memory_estimate_mb
        self.data_quality = data_quality or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "source_type": self.source_type,
            "filename": self.filename,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns": [c.to_dict() for c in self.columns],
            "numeric_columns": self.numeric_columns,
            "categorical_columns": self.categorical_columns,
            "datetime_columns": self.datetime_columns,
            "missing_columns": self.missing_columns,
            "duplicate_count": self.duplicate_count,
            "constant_columns": self.constant_columns,
            "likely_id_columns": self.likely_id_columns,
            "potential_target_columns": self.potential_target_columns,
            "memory_estimate_mb": self.memory_estimate_mb,
            "data_quality": self.data_quality,
        }


class Insight:
    """A deterministic insight detected from data analysis."""

    def __init__(
        self,
        type: str,
        severity: str,
        title: str,
        description: Optional[str] = None,
        evidence: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None,
        confidence: float = 1.0,
    ):
        self.type = type
        self.severity = severity
        self.title = title
        self.description = description
        self.evidence = evidence or {}
        self.columns = columns or []
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "columns": self.columns,
            "confidence": self.confidence,
        }


class ChartSpec:
    """A JSON-serializable chart specification."""

    def __init__(
        self,
        type: str,
        title: str,
        x: Optional[str] = None,
        y: Optional[str] = None,
        column: Optional[str] = None,
        aggregation: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        self.type = type
        self.title = title
        self.x = x
        self.y = y
        self.column = column
        self.aggregation = aggregation
        self.extra = extra or {}

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "type": self.type,
            "title": self.title,
        }
        if self.x is not None:
            d["x"] = self.x
        if self.y is not None:
            d["y"] = self.y
        if self.column is not None:
            d["column"] = self.column
        if self.aggregation is not None:
            d["aggregation"] = self.aggregation
        d.update(self.extra)
        return d
