"""Deterministic Data Analyst Specialist for TrustLens"""
import io
import csv
import math
import statistics
from typing import Any, Dict, List, Optional
from app.specialists.base import BaseSpecialist


class DataAnalyst(BaseSpecialist):
    """
    Deterministic Statistical & Profiling Specialist for structured tables and CSV files.
    Performs data profiling, statistical distribution analysis, anomaly detection,
    and extracts numerical insights with exact calculation provenance.
    """

    def __init__(self):
        super().__init__(
            name="Data Analyst",
            description="Performs deterministic statistical profiling, correlation, and data quality analysis on tabular data",
            capabilities=["data_profiling", "statistical_analysis", "data_quality", "insight_extraction"]
        )

    async def analyze(self, workspace_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        csv_text = context.get("raw_content", "") or context.get("text", "")
        filename = context.get("filename", "dataset.csv")

        if not csv_text.strip() or ("," not in csv_text and "\t" not in csv_text):
            return {"is_tabular": False, "error": "Not a recognized tabular dataset"}

        profile = self.profile_table(csv_text, filename)
        return {"is_tabular": True, **profile}

    def profile_table(self, csv_text: str, filename: str = "dataset.csv") -> Dict[str, Any]:
        """Parses CSV and computes comprehensive statistical profiles deterministically."""
        delimiter = "\t" if "\t" in csv_text.splitlines()[0] else ","
        reader = csv.reader(io.StringIO(csv_text.strip()), delimiter=delimiter)
        rows = list(reader)

        if len(rows) < 2:
            return {"is_tabular": False, "error": "Table has insufficient rows"}

        headers = [h.strip() for h in rows[0]]
        data_rows = rows[1:]
        row_count = len(data_rows)
        col_count = len(headers)

        columns_profile: Dict[str, Any] = {}
        numeric_columns: Dict[str, List[float]] = {}

        for col_idx, col_name in enumerate(headers):
            values = []
            null_count = 0
            for r in data_rows:
                val = r[col_idx].strip() if col_idx < len(r) else ""
                if val == "" or val.lower() in {"null", "nan", "none", "na"}:
                    null_count += 1
                else:
                    values.append(val)

            # Detect data type
            numeric_vals = []
            for v in values:
                # Strip currency symbols and commas
                clean_v = v.replace("$", "").replace("€", "").replace(",", "").replace("%", "")
                try:
                    num = float(clean_v)
                    numeric_vals.append(num)
                except ValueError:
                    pass

            is_numeric = len(numeric_vals) >= (len(values) * 0.8) and len(numeric_vals) > 0

            col_meta: Dict[str, Any] = {
                "name": col_name,
                "type": "Numeric" if is_numeric else "Categorical",
                "total_count": row_count,
                "null_count": null_count,
                "null_percentage": round((null_count / row_count) * 100, 1),
                "distinct_count": len(set(values))
            }

            if is_numeric and numeric_vals:
                numeric_columns[col_name] = numeric_vals
                col_meta["stats"] = {
                    "min": round(min(numeric_vals), 2),
                    "max": round(max(numeric_vals), 2),
                    "mean": round(statistics.mean(numeric_vals), 2),
                    "median": round(statistics.median(numeric_vals), 2),
                    "sum": round(sum(numeric_vals), 2),
                    "std_dev": round(statistics.stdev(numeric_vals), 2) if len(numeric_vals) > 1 else 0.0
                }

                # Outlier detection via IQR
                if len(numeric_vals) >= 4:
                    sorted_vals = sorted(numeric_vals)
                    q1 = sorted_vals[len(sorted_vals) // 4]
                    q3 = sorted_vals[(len(sorted_vals) * 3) // 4]
                    iqr = q3 - q1
                    lower_bound = q1 - (1.5 * iqr)
                    upper_bound = q3 + (1.5 * iqr)
                    outliers = [v for v in numeric_vals if v < lower_bound or v > upper_bound]
                    col_meta["outliers_count"] = len(outliers)
            else:
                col_meta["stats"] = {
                    "top_values": list(set(values))[:5]
                }

            columns_profile[col_name] = col_meta

        # Insights Extraction
        insights = []
        for col_name, nums in numeric_columns.items():
            mean_val = statistics.mean(nums)
            max_val = max(nums)
            min_val = min(nums)
            insights.append({
                "type": "SUMMARY",
                "finding": f"Column '{col_name}' ranges from {min_val} to {max_val} with an average of {round(mean_val, 2)}.",
                "provenance": f"Calculated over {len(nums)} rows from {filename}",
                "implication": f"Primary distribution metric for {col_name}."
            })

        # Correlation between first two numeric columns if available
        num_keys = list(numeric_columns.keys())
        if len(num_keys) >= 2:
            k1, k2 = num_keys[0], num_keys[1]
            v1, v2 = numeric_columns[k1], numeric_columns[k2]
            min_len = min(len(v1), len(v2))
            if min_len > 2 and len(set(v1[:min_len])) > 1 and len(set(v2[:min_len])) > 1:
                try:
                    corr = statistics.correlation(v1[:min_len], v2[:min_len])
                    insights.append({
                        "type": "CORRELATION",
                        "finding": f"Statistical correlation between '{k1}' and '{k2}' is {round(corr, 3)}.",
                        "provenance": f"Pearson correlation formula computed over {min_len} paired values",
                        "implication": "Strong relationship detected" if abs(corr) > 0.7 else "Moderate/weak relationship"
                    })
                except Exception:
                    pass

        return {
            "filename": filename,
            "row_count": row_count,
            "col_count": col_count,
            "headers": headers,
            "columns_profile": columns_profile,
            "insights": insights,
            "data_quality": {
                "complete_rows": sum(1 for r in data_rows if all(c.strip() != "" for c in r)),
                "total_rows": row_count,
                "has_outliers": any(c.get("outliers_count", 0) > 0 for c in columns_profile.values())
            }
        }
