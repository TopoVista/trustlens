"""IO helpers."""

import json
from pathlib import Path


def read_json(path):
    with Path(path).open('r', encoding='utf-8') as f:
        return json.load(f)


def write_json(obj, path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
