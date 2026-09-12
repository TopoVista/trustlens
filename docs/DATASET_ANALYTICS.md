# Dataset analytics API

TrustLens includes a lightweight backend dataset-analysis surface alongside the
document workspace product. It is server API functionality; the current React
evidence desk does not expose a dedicated dataset screen.

## Design

Dataset sessions store metadata and a source reference rather than a globally
resident DataFrame. Profiling, EDA, insights, chart specifications, dashboard
specifications, forecasting, and anomaly calls produce JSON suitable for a
frontend renderer. The implementation keeps heavy analytical dependencies out
of the normal application startup path.

## Current routes

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/datasets/upload` | Upload and create a dataset session. |
| `POST` | `/datasets/profile` | Profile dataset content. |
| `GET` | `/datasets` | List datasets for the authenticated user context. |
| `GET` | `/datasets/{dataset_id}` | Read one dataset session and profile. |
| `POST` | `/datasets/{dataset_id}/eda` | Request deterministic exploratory analysis. |
| `GET` | `/datasets/{dataset_id}/insights` | Return detected insights. |
| `GET` | `/datasets/{dataset_id}/charts` | Return chart specifications. |
| `POST` | `/datasets/{dataset_id}/query` | Ask a constrained dataset question or submit a validated plan. |
| `GET` | `/datasets/{dataset_id}/dashboard` | Return a frontend-renderable dashboard specification. |
| `POST` | `/datasets/{dataset_id}/forecast` | Request optional forecast output. |
| `POST` | `/datasets/{dataset_id}/anomalies` | Request optional anomaly output. |
| `DELETE` | `/datasets/{dataset_id}` | Remove the session and its associated stored file. |

These endpoints live in `backend/app/api/routes.py`; core modules live under
`backend/app/data` and `backend/app/analytics`.

## Security and limits

Dataset operations use the caller context supplied to the backend and should
not evaluate generated arbitrary code. The query route accepts a limited
natural-language question or a validated JSON plan. Profile and analysis size,
format, and optional-dependency behavior should be tested against the target
deployment before claiming support for a particular large or binary dataset.

## Validation

Run the analytics-focused tests from the repository root:

```powershell
pytest tests/test_analytics.py -q
```

Keep this document aligned with the actual route names. Earlier drafts used
`/api/datasets/*`; the current route declarations use `/datasets/*`.
