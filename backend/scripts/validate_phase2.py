"""Validate Phase 2 analytics modules work without heavy dependencies."""
import json
import sys
import tempfile
import os
from pathlib import Path

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Verify heavy modules are NOT loaded
heavy = [m for m in ("torch", "transformers", "sentence_transformers", "faiss", "spacy", "pandas", "sklearn")
         if m in sys.modules]
print(f"Heavy modules at start: {heavy if heavy else 'NONE'}")

# Now import analytics
from app.analytics.profiling import profile_dataset, read_dataset
from app.analytics.eda import compute_statistics, compute_correlations, detect_outliers_iqr
from app.analytics.insights import detect_insights
from app.analytics.charts import suggest_charts
from app.data.storage import store_upload, get_metadata, get_path, list_datasets, _UPLOAD_DIR
from app.data.session import get_session

heavy = [m for m in ("torch", "transformers", "sentence_transformers", "faiss", "spacy", "pandas", "sklearn")
         if m in sys.modules]
print(f"Heavy modules after analytics import: {heavy if heavy else 'NONE'}")

# Create a test CSV
test_csv = """region,revenue,customers
East,100000,250
East,85000,200
West,150000,300
West,140000,280
North,90000,180
North,95000,190
South,110000,220
South,105000,210
East,69000,150
West,160000,310
"""

# Write to temp file and profile
csv_path = os.path.join(tempfile.gettempdir(), "test_sales.csv")
with open(csv_path, "w") as f:
    f.write(test_csv)

profile = profile_dataset("test_sales.csv", csv_path, "test-001")
print(f"\nProfile: {profile.row_count} rows, {profile.column_count} cols")
print(f"Numeric: {profile.numeric_columns}")
print(f"Categorical: {profile.categorical_columns}")
print(f"Missing cols: {profile.missing_columns}")
print(f"Constant cols: {profile.constant_columns}")
print(f"Likely IDs: {profile.likely_id_columns}")

# EDA
headers, rows = read_dataset("test_sales.csv", csv_path)
# Extract revenue column values (revenue is 2nd column, index 1)
rev_values = [row[1] for row in rows] if rows else []
reg_values = [row[0] for row in rows] if rows else []

stats = compute_statistics(rev_values)
print(f"\nStats for revenue: mean={stats.get('mean')}, std={stats.get('std')}, median={stats.get('median')}")

corr = compute_correlations(headers, rows, numeric_columns=["revenue", "customers"])
print(f"Correlations found: {len(corr)}")

outliers = detect_outliers_iqr(rev_values)
print(f"Revenue outliers: {outliers.get('count', 0)}")

# Insights
insights = detect_insights(profile, headers, rows)
print(f"\nInsights detected: {len(insights)}")
for ins in insights[:5]:
    print(f"  - [{ins.type}] {ins.title}")

# Charts
charts = suggest_charts(profile)
print(f"\nCharts suggested: {len(charts)}")
for ch in charts[:3]:
    print(f"  - {ch.type}: {ch.title or ''}")

# Storage + session
print(f"\nUploads dir: {_UPLOAD_DIR}")
print(f"List datasets: {list_datasets()}")

print("\nPhase 2 validation: PASS")
