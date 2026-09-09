"""Regression test for the corpus rebuild lock used during embedding drift."""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def test_search_skips_parallel_dimension_rebuild(monkeypatch):
    import numpy as np
    from app.pipeline import retriever

    monkeypatch.setattr(retriever, "_load_resources", lambda: (np.zeros((1, 2), dtype=np.float32), [{"id": "x", "text": "x"}]))

    class Model:
        def encode(self, *_args, **_kwargs):
            return np.zeros((1, 3), dtype=np.float32)

    monkeypatch.setattr(retriever, "get_embedding_model", lambda: Model())
    assert retriever._rebuild_lock.acquire(blocking=False)
    try:
        assert retriever._search("test", 1) == []
    finally:
        retriever._rebuild_lock.release()
