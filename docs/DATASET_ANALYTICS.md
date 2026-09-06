# Dataset Analytics Architecture

Phase 2 of the TrustLens lightweight data-science engine. This document describes
the **DatasetSession**, **DatasetProfiler**, **deterministic EDA engine**,
**insight engine**, **chart spec engine**, and **optional LLM integration** for
user-provided tabular data.

## Goals

- "Give me your data and ask me anything about it."
- Deterministic analytics compute the facts; the LLM interprets them.
- Keep the Render Free (512 MiB) baseline at ~80 MB idle.
- Keep `pandas` / `sklearn` / `torch` out of the production import path.

## Architecture overview

```
User Dataset
     |
     v
DatasetSession  (references data, holds metadata — NO global DataFrame)
     |
     v
DatasetProfiler  (stdlib + numpy, streaming readers, bounded sampling)
     |
     +----------+
     |          |
     v          v
  Insights    Chart Specs   (deterministic)
   Engine       Engine
     |            |
     +-----+------+
           |
           v
   Optional External LLM  (interpretation only, receives JSON not raw bytes)
           |
           v
    Natural-language response
```

## DatasetSession

```python
# backend/app/data/session.py
class DatasetSession:
    dataset_id, source_type, source_reference, filename
    profile: DatasetProfile
    transformations: list[dict]
    generated_artifacts: list[dict]
    analysis_history: list[dict]
```

- Sessions are referenced by `dataset_id` and **store file paths**, not DataFrames.
- Created lazily on first upload/analysis request.
- Destroyed via DELETE endpoint (evicts from cache + file).

## Supported formats

| Format | Reader | Optional? |
|--------|--------|-----------|
| CSV    | stdlib `csv.DictReader` | no |
| JSON   | stdlib `json` (records) | no |
| Parquet| `pyarrow` or `fastparquet` | yes — graceful error if missing |
| Excel  | `openpyxl` | yes — graceful error if missing |
| TXT    | stdlib | no |

If an optional reader is missing, the API returns:
```json
{"error": "Optional dependency 'openpyxl' required for Excel files. ..."}
```

## Dataset Profiler

Produces `DatasetProfile`:

```python
column_metadata: list[ColumnProfile]  # per-column
row_count, column_count
numeric_columns, categorical_columns, datetime_columns
missing_columns, duplicate_count
constant_columns, likely_id_columns, potential_target_columns
memory_estimate
```

Per-column (`ColumnProfile`):
- `dtype`, `null_count`, `null_percentage`
- `unique_count`, `unique_percentage`, `sample_values` (3)
- Numeric: `min, max, mean, median, std, q1, q3` (only if ≤ N rows or on sample)
- Categorical: `top_values`, `frequencies`
- Datetime: `min_date`, `max_date`, inferred frequency

### Large-dataset safety

| Threshold | Mode |
|-----------|------|
| ≤ 10,000 rows | full profiling |
| 10,001 – 1,000,000 rows | 10,000-row bounded statistics + full metadata |
| > 1,000,000 rows | 10,000-row sample for stats; metadata from first/None checks only |

All sampling uses streaming — no second full DataFrame copy is ever held.

## EDA engine (deterministic)

```python
app/analytics/eda.py
compute_statistics(values) -> dict
compute_correlations(headers, rows, numeric_cols) -> list
detect_outliers_iqr(values) -> dict
```

No LLM. No pandas/sklearn. Uses `math` and `numpy` only for correlation matrices
(lazily imported within `compute_correlations`).

## Insight engine

```python
app/analytics/insights.py
detect_insights(profile, headers, rows) -> list[Insight]
```

Detects: missingness, duplicates, constant columns, dominant categories,
high-cardinality columns, numeric outliers (IQR), strong correlations (|r| ≥ 0.7),
and change/seasonality where deterministically detectable.

Result models are typed (`Insight`, `ChartSpec`, `ColumnProfile`, etc.) and
JSON-serializable.

## Chart spec engine

```python
app/analytics/charts.py
suggest_charts(profile) -> list[ChartSpec]
```

Rules:
- datetime + numeric → line
- categorical + numeric → bar (sum by default)
- single numeric → histogram
- single categorical → frequency bar
- numeric × numeric → scatter
- constant/categorical-only datasets → no charts

## API endpoints

All datasets are **user-scoped** (workspace isolation via `x-user-id`).

```
POST   /api/datasets/upload        # parse + store + return dataset_id + profile
GET    /api/datasets               # list this user's datasets
GET    /api/datasets/{id}          # get session + profile
POST   /api/datasets/{id}/insights # run insight + chart detection
POST   /api/datasets/{id}/ask      # NL question (LLM optional; deterministic fallback)
DELETE /api/datasets/{id}          # delete + evict
```

## LLM behavior

- With `OPENAI_API_KEY`: deterministic results + LLM interpretation. LLM receives
  `DatasetProfile`, `Insight` list, and `ChartSpec` list — never the raw CSV bytes.
- Without `OPENAI_API_KEY`: structured results returned; NL questions return a
  deterministic templated explanation of the computed insights.

## Memory

- `import app.main` does **not** import pandas/sklearn/torch/transformers.
- `numpy` is the only third-party runtime import (part of requirements-prod.txt).
- `validate_phase2.py` asserts: heavy modules `NONE`, analytics work, RSS < 150 MB.

## Testing

```
python -m pytest tests/test_analytics.py -v  # 40 tests
python backend/scripts/validate_phase2.py      # smoke + memory check
python backend/scripts/profile_startup.py      # import + RSS profile
```

## Specialist registry

New specialists are registered in `app/planner/registry.py`:
```
profiler → DataProfiler
eda → EDAAnalyst
insight_analyst → InsightAnalyst
visualization_analyst → VisualizationAnalyst
anomaly_analyst → AnomalyAnalyst
```

Each specialist exposes `(name, description, capabilities, analyze(...))`.
Analytics imports are **inside** `analyze()` — specialists themselves import nothing
heavy at construction.
