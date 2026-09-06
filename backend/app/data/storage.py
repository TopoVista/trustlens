"""Lightweight file-backed storage for uploaded datasets.

Stores raw uploaded bytes on disk under backend/data/uploads/ and tracks
metadata in a small JSON index. Avoids keeping file contents in RAM.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_UPLOAD_DIR = Path(__file__).resolve().parents[2] / "data" / "uploads"
_INDEX_PATH = _UPLOAD_DIR / "index.json"


def _ensure_dirs() -> None:
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    if not _INDEX_PATH.exists():
        _INDEX_PATH.write_text("{}", encoding="utf-8")


def _load_index() -> Dict[str, Any]:
    _ensure_dirs()
    try:
        return json.loads(_INDEX_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_index(index: Dict[str, Any]) -> None:
    _ensure_dirs()
    _INDEX_PATH.write_text(json.dumps(index, indent=2, default=str), encoding="utf-8")


def store_upload(filename: str, content: bytes, source_type: str) -> str:
    """Persist uploaded bytes and return a generated dataset_id."""
    dataset_id = f"ds_{uuid.uuid4().hex[:12]}"
    safe_name = Path(filename).name or "dataset"
    target = _UPLOAD_DIR / f"{dataset_id}_{safe_name}"
    target.write_bytes(content)

    index = _load_index()
    index[dataset_id] = {
        "dataset_id": dataset_id,
        "filename": safe_name,
        "source_type": source_type,
        "stored_path": str(target),
        "size_bytes": len(content),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_index(index)
    return dataset_id


def get_metadata(dataset_id: str) -> Optional[Dict[str, Any]]:
    return _load_index().get(dataset_id)


def get_path(dataset_id: str) -> Optional[Path]:
    meta = get_metadata(dataset_id)
    if not meta:
        return None
    p = Path(meta["stored_path"])
    return p if p.exists() else None


def list_datasets() -> Dict[str, Any]:
    return _load_index()


def delete_dataset(dataset_id: str) -> bool:
    index = _load_index()
    meta = index.pop(dataset_id, None)
    if meta:
        try:
            Path(meta["stored_path"]).unlink(missing_ok=True)
        except OSError:
            pass
    _save_index(index)
    return meta is not None