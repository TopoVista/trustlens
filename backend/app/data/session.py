"""DatasetSession — lightweight reference to an uploaded dataset.

The session stores metadata and schema information but does NOT hold the
full dataset permanently in RAM. Data is read from disk on demand.
"""
from typing import Any, Dict, List, Optional

from app.data.storage import get_metadata, get_path


class DatasetSession:
    """References a persisted dataset and caches lightweight metadata only."""

    def __init__(self, dataset_id: str):
        self.dataset_id = dataset_id
        self._meta: Optional[Dict[str, Any]] = None
        self._schema: Optional[Dict[str, Any]] = None

    @property
    def meta(self) -> Optional[Dict[str, Any]]:
        if self._meta is None:
            self._meta = get_metadata(self.dataset_id)
        return self._meta

    @property
    def exists(self) -> bool:
        return self.meta is not None

    @property
    def file_path(self):
        from pathlib import Path
        return get_path(self.dataset_id)

    @property
    def source_type(self) -> str:
        return (self.meta or {}).get("source_type", "unknown")

    @property
    def filename(self) -> str:
        return (self.meta or {}).get("filename", "dataset")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "filename": self.filename,
            "source_type": self.source_type,
            "exists": self.exists,
            **(self.meta or {}),
        }


class SessionManager:
    """Bounded in-memory registry of active DatasetSessions."""

    def __init__(self, max_sessions: int = 32):
        self._sessions: Dict[str, DatasetSession] = {}
        self._max = max_sessions

    def get(self, dataset_id: str) -> DatasetSession:
        if dataset_id not in self._sessions:
            self._sessions[dataset_id] = DatasetSession(dataset_id)
            self._evict()
        return self._sessions[dataset_id]

    def evict(self, dataset_id: str) -> None:
        """Drop a cached session so deleted datasets are not served stale."""
        self._sessions.pop(dataset_id, None)

    def _evict(self) -> None:
        while len(self._sessions) > self._max:
            oldest = next(iter(self._sessions))
            self._sessions.pop(oldest, None)


_sessions = SessionManager()


def get_session(dataset_id: str) -> DatasetSession:
    return _sessions.get(dataset_id)


def evict_session(dataset_id: str) -> None:
    _sessions.evict(dataset_id)