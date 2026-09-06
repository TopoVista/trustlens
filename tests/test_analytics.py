"""Phase 2 dataset analytics engine tests.

Covers: DatasetProfiler, EDA engine, chart specs, deterministic insights,
dataset storage/session lifecycle, dataset API endpoints, and startup
memory guarantees (no heavy analytics/ML modules).
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure backend package is in python path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.analytics.profiling import profile_dataset, read_dataset  # noqa: E402
from app.analytics.eda import (  # noqa: E402
    compute_correlations,
    compute_statistics,
    detect_outliers_iqr,
    detect_outliers_zscore,
)
from app.analytics.insights import detect_insights  # noqa: E402
from app.analytics.charts import suggest_charts  # noqa: E402
from app.data import storage as dataset_storage  # noqa: E402

HEAVY_MODULES = ("torch", "transformers", "sentence_transformers", "faiss", "spacy", "pandas", "sklearn")

SAMPLE_CSV = (
    "region,revenue,customers\n"
    "East,100000,250\n"
    "East,85000,200\n"
    "West,150000,300\n"
    "West,140000,280\n"
    "North,90000,180\n"
    "North,95000,190\n"
    "South,110000,220\n"
    "South,105000,210\n"
)


@pytest.fixture()
def sample_csv(tmp_path):
    path = tmp_path / "sales.csv"
    path.write_text(SAMPLE_CSV, encoding="utf-8")
    return str(path)


@pytest.fixture()
def stored_dataset(sample_csv):
    content = Path(sample_csv).read_bytes()
    dataset_id = dataset_storage.store_upload("sales.csv", content, "csv")
    yield dataset_id
    dataset_storage.delete_dataset(dataset_id)


def _write_csv(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return str(path)


# ---------------------------------------------------------------------------
# DatasetProfiler
# ---------------------------------------------------------------------------


class TestProfiler:
    def test_empty_dataset(self, tmp_path):
        path = _write_csv(tmp_path, "empty.csv", "")
        profile = profile_dataset("empty.csv", path, "ds-empty")
        assert profile.row_count == 0
        assert profile.column_count == 0
        assert profile.columns == []

    def test_normal_dataset(self, sample_csv):
        profile = profile_dataset("sales.csv", sample_csv, "ds-normal")
        assert profile.row_count == 8
        assert profile.column_count == 3
        assert set(profile.numeric_columns) == {"revenue", "customers"}
        assert "region" in profile.categorical_columns
        assert profile.data_quality["completeness_pct"] == 100.0

    def test_missing_values(self, tmp_path):
        path = _write_csv(tmp_path, "missing.csv", "a,b,c\n1,,x\n2,y,\n3,z,w\n")
        profile = profile_dataset("missing.csv", path, "ds-missing")
        assert set(profile.missing_columns) == {"b", "c"}
        col_b = next(c for c in profile.columns if c.name == "b")
        assert col_b.null_count == 1
        assert col_b.null_percentage > 0

    def test_duplicate_rows(self, tmp_path):
        path = _write_csv(tmp_path, "dupes.csv", "a,b\n1,x\n1,x\n2,y\n")
        profile = profile_dataset("dupes.csv", path, "ds-dupes")
        assert profile.duplicate_count == 1
        assert profile.data_quality["duplicate_rate_pct"] > 0

    def test_numeric_columns(self, sample_csv):
        profile = profile_dataset("sales.csv", sample_csv, "ds-num")
        revenue = next(c for c in profile.columns if c.name == "revenue")
        assert revenue.dtype == "numeric"
        assert revenue.stats["min"] == 85000
        assert revenue.stats["max"] == 150000

    def test_categorical_columns(self, sample_csv):
        profile = profile_dataset("sales.csv", sample_csv, "ds-cat")
        region = next(c for c in profile.columns if c.name == "region")
        assert region.dtype == "categorical"
        assert region.stats["top_values"][0]["count"] == 2

    def test_datetime_columns(self, tmp_path):
        path = _write_csv(
            tmp_path, "dates.csv",
            "date,amount\n2024-01-01,10\n2024-01-02,20\n2024-01-03,30\n",
        )
        profile = profile_dataset("dates.csv", path, "ds-dates")
        assert "date" in profile.datetime_columns

    def test_constant_columns(self, tmp_path):
        path = _write_csv(tmp_path, "constant.csv", "a,const\n1,same\n2,same\n3,same\n")
        profile = profile_dataset("constant.csv", path, "ds-const")
        assert profile.constant_columns == ["const"]

    def test_likely_id_columns(self, tmp_path):
        path = _write_csv(
            tmp_path, "ids.csv",
            "user_id,score\nusr_001,10\nusr_002,20\nusr_003,30\nusr_004,40\nusr_005,50\n",
        )
        profile = profile_dataset("ids.csv", path, "ds-ids")
        assert "user_id" in profile.likely_id_columns
        path2 = _write_csv(tmp_path, "seq.csv", "idx,score\n1,10\n2,20\n3,30\n4,40\n5,50\n")
        profile2 = profile_dataset("seq.csv", path2, "ds-seq")
        assert "idx" in profile2.likely_id_columns

    def test_measurements_not_flagged_as_ids(self, sample_csv):
        profile = profile_dataset("sales.csv", sample_csv, "ds-meas")
        assert "revenue" not in profile.likely_id_columns
        assert "customers" not in profile.likely_id_columns

    def test_json_dataset(self, tmp_path):
        path = tmp_path / "data.json"
        path.write_text(
            '[{"name": "a", "value": 1}, {"name": "b", "value": 2}, '
            '{"name": "c", "value": 3}]',
            encoding="utf-8",
        )
        profile = profile_dataset("data.json", str(path), "ds-json")
        assert profile.row_count == 3
        assert set(profile.numeric_columns) == {"value"}


# ---------------------------------------------------------------------------
# EDA engine
# ---------------------------------------------------------------------------


class TestEDA:
    def test_statistics(self):
        stats = compute_statistics([1, 2, 3, 4, 5])
        assert stats["count"] == 5
        assert stats["min"] == 1
        assert stats["max"] == 5
        assert stats["mean"] == 3.0
        assert stats["median"] == 3.0

    def test_statistics_empty(self):
        assert compute_statistics([]) == {}

    def test_correlations(self, sample_csv):
        headers, rows = read_dataset("sales.csv", sample_csv)
        corrs = compute_correlations(headers, rows, ["revenue", "customers"])
        assert len(corrs) == 1
        entry = corrs[0]
        assert entry["column_a"] == "revenue"
        assert entry["column_b"] == "customers"
        assert abs(entry["correlation"]) > 0.5

    def test_outliers_iqr(self):
        values = [10, 11, 12, 13, 14, 15, 100]
        result = detect_outliers_iqr(values)
        assert result["count"] >= 1
        assert result["threshold_high"] is not None

    def test_outliers_iqr_too_few_values(self):
        assert detect_outliers_iqr([1, 2, 3])["count"] == 0

    def test_outliers_zscore(self):
        # Extreme outlier with enough baseline samples so the z-score exceeds 3
        values = [10] * 19 + [500]
        assert detect_outliers_zscore(values)["count"] == 1


# ---------------------------------------------------------------------------
# Chart specification engine
# ---------------------------------------------------------------------------


class TestCharts:
    def test_numeric_histogram(self, sample_csv):
        profile = profile_dataset("sales.csv", sample_csv, "ds-chart")
        charts = suggest_charts(profile)
        histograms = [c for c in charts if c.type == "histogram"]
        assert len(histograms) == 2  # revenue + customers
        assert all(c.column in {"revenue", "customers"} for c in histograms)

    def test_categorical_frequency(self, sample_csv):
        profile = profile_dataset("sales.csv", sample_csv, "ds-freq")
        charts = suggest_charts(profile)
        frequencies = [c for c in charts if c.type == "frequency"]
        assert len(frequencies) == 1
        assert frequencies[0].column == "region"

    def test_time_series_line(self, tmp_path):
        path = _write_csv(
            tmp_path, "ts.csv",
            "date,value\n2024-01-01,1\n2024-01-02,2\n2024-01-03,3\n2024-01-04,4\n",
        )
        profile = profile_dataset("ts.csv", path, "ds-ts")
        charts = suggest_charts(profile)
        lines = [c for c in charts if c.type == "line"]
        assert lines and lines[0].x == "date" and lines[0].y == "value"

    def test_scatter_for_numeric_pairs(self, sample_csv):
        profile = profile_dataset("sales.csv", sample_csv, "ds-scatter")
        charts = suggest_charts(profile)
        scatters = [c for c in charts if c.type == "scatter"]
        assert scatters
        assert {(s.x, s.y) for s in scatters} == {("revenue", "customers")}

    def test_charts_bounded_at_20(self, tmp_path):
        path = _write_csv(tmp_path, "wide.csv", "a,b,c,d,e,f\n1,2,3,4,5,6\n7,8,9,10,11,12\n")
        profile = profile_dataset("wide.csv", path, "ds-wide")
        assert len(suggest_charts(profile)) <= 20



# ---------------------------------------------------------------------------
# Insight engine
# ---------------------------------------------------------------------------


class TestInsights:
    def test_missingness_insight(self, tmp_path):
        path = _write_csv(tmp_path, "miss.csv", "a,b\n1,\n2,\n3,\n4,x\n")
        profile = profile_dataset("miss.csv", path, "ds-miss")
        headers, rows = read_dataset("miss.csv", path)
        insights = detect_insights(profile, headers, rows)
        missing = [i for i in insights if i.type == "missingness"]
        assert missing and missing[0].columns == ["b"]

    def test_outlier_insight(self, tmp_path):
        path = _write_csv(tmp_path, "out.csv", "val\n10\n11\n12\n13\n14\n15\n100\n")
        profile = profile_dataset("out.csv", path, "ds-out")
        headers, rows = read_dataset("out.csv", path)
        insights = detect_insights(profile, headers, rows)
        assert any(i.type == "outliers" and i.columns == ["val"] for i in insights)

    def test_category_dominance_insight(self, tmp_path):
        path = _write_csv(tmp_path, "dom.csv", "cat,val\nEast,1\nEast,2\nEast,3\nWest,4\n")
        profile = profile_dataset("dom.csv", path, "ds-dom")
        headers, rows = read_dataset("dom.csv", path)
        insights = detect_insights(profile, headers, rows)
        dominance = [i for i in insights if i.type == "category_dominance"]
        assert dominance and dominance[0].evidence["top_category"] == "East"

    def test_correlation_insight(self, sample_csv):
        profile = profile_dataset("sales.csv", sample_csv, "ds-corr")
        headers, rows = read_dataset("sales.csv", sample_csv)
        insights = detect_insights(profile, headers, rows)
        corr = [i for i in insights if i.type == "correlation"]
        assert corr and corr[0].evidence["strength"] == "strong"

    def test_no_quality_insights_for_clean_data(self, tmp_path):
        path = _write_csv(tmp_path, "clean.csv", "a,b\n1,10\n2,20\n3,30\n4,40\n")
        profile = profile_dataset("clean.csv", path, "ds-clean")
        headers, rows = read_dataset("clean.csv", path)
        insights = detect_insights(profile, headers, rows)
        assert all(i.type != "missingness" for i in insights)
        assert all(i.type != "duplicates" for i in insights)


# ---------------------------------------------------------------------------
# Storage + session lifecycle
# ---------------------------------------------------------------------------


class TestStorageAndSession:
    def test_store_and_delete_roundtrip(self, sample_csv):
        content = Path(sample_csv).read_bytes()
        dataset_id = dataset_storage.store_upload("roundtrip.csv", content, "csv")
        try:
            meta = dataset_storage.get_metadata(dataset_id)
            assert meta and meta["filename"] == "roundtrip.csv"
            assert dataset_storage.get_path(dataset_id) is not None
            assert dataset_id in dataset_storage.list_datasets()
        finally:
            assert dataset_storage.delete_dataset(dataset_id)
        assert dataset_storage.get_metadata(dataset_id) is None

    def test_session_lifecycle(self, stored_dataset):
        from app.data.session import get_session

        session = get_session(stored_dataset)
        assert session.exists
        assert session.source_type == "csv"
        assert session.file_path is not None
        assert session.to_dict()["dataset_id"] == stored_dataset

    def test_session_for_missing_dataset(self):
        from app.data.session import get_session

        assert not get_session("ds_does_not_exist").exists

    def test_delete_missing_dataset(self):
        assert dataset_storage.delete_dataset("ds_missing") is False


# ---------------------------------------------------------------------------
# Dataset API endpoints
# ---------------------------------------------------------------------------


class TestDatasetAPI:
    @pytest.fixture(autouse=True)
    def _client(self):
        from app.main import app

        self.client = TestClient(app)
        self.headers = {"x-user-id": "analytics_test_user"}
        self.created_ids = []
        yield
        for dataset_id in self.created_ids:
            dataset_storage.delete_dataset(dataset_id)

    def _upload(self, filename="sales.csv", content=None):
        body = content if content is not None else SAMPLE_CSV.encode()
        resp = self.client.post(
            f"/datasets/upload?filename={filename}&source_type=csv",
            content=body,
            headers=self.headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        self.created_ids.append(data["dataset_id"])
        return data

    def test_upload_and_profile(self):
        data = self._upload()
        assert data["dataset_id"].startswith("ds_")
        resp = self.client.post(
            f"/datasets/profile?dataset_id={data['dataset_id']}",
            headers=self.headers,
        )
        assert resp.status_code == 200, resp.text
        profile = resp.json()
        assert profile["row_count"] == 8
        assert "revenue" in profile["numeric_columns"]

    def test_upload_empty_body_rejected(self):
        resp = self.client.post(
            "/datasets/upload?filename=x.csv", content=b"", headers=self.headers
        )
        assert resp.status_code == 400

    def test_eda_endpoint(self):
        data = self._upload()
        resp = self.client.post(f"/datasets/{data['dataset_id']}/eda", headers=self.headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["dataset_id"] == data["dataset_id"]
        assert "revenue" in body["statistics"]
        assert set(body["statistics"]["revenue"]) >= {"mean", "median", "std", "min", "max"}

    def test_insights_endpoint(self):
        data = self._upload()
        resp = self.client.get(f"/datasets/{data['dataset_id']}/insights", headers=self.headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert isinstance(body["insights"], list)
        assert any(i["type"] == "correlation" for i in body["insights"])

    def test_charts_endpoint(self):
        data = self._upload()
        resp = self.client.get(f"/datasets/{data['dataset_id']}/charts", headers=self.headers)
        assert resp.status_code == 200, resp.text
        charts = resp.json()["charts"]
        assert charts
        assert all("type" in c and "title" in c for c in charts)

    def test_list_get_delete(self):
        data = self._upload()
        listing = self.client.get("/datasets", headers=self.headers).json()
        assert any(d["id"] == data["dataset_id"] for d in listing["datasets"])

        detail = self.client.get(f"/datasets/{data['dataset_id']}", headers=self.headers).json()
        assert detail["filename"] == "sales.csv"

        deleted = self.client.delete(f"/datasets/{data['dataset_id']}", headers=self.headers)
        assert deleted.status_code == 200
        assert deleted.json()["status"] == "deleted"

        missing = self.client.get(f"/datasets/{data['dataset_id']}", headers=self.headers)
        assert missing.status_code == 404

    def test_404_for_unknown_dataset(self):
        resp = self.client.post("/datasets/profile?dataset_id=ds_nope", headers=self.headers)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Startup memory guarantees
# ---------------------------------------------------------------------------


class TestStartupMemory:
    def test_import_app_main_does_not_load_heavy_modules(self):
        import subprocess

        script = (
            "import sys; import app.main; "
            f"heavy=[m for m in {HEAVY_MODULES} if m in sys.modules]; "
            "print('HEAVY:', heavy)"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=str(backend_dir),
        )
        assert result.returncode == 0, result.stderr
        assert "HEAVY: []" in result.stdout

    def test_analytics_import_does_not_load_heavy_modules(self):
        import subprocess

        script = (
            "import sys; "
            "from app.analytics import profiling, eda, insights, charts; "
            "from app.data import storage, session; "
            f"heavy=[m for m in {HEAVY_MODULES} if m in sys.modules]; "
            "print('HEAVY:', heavy)"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=str(backend_dir),
        )
        assert result.returncode == 0, result.stderr
        assert "HEAVY: []" in result.stdout

