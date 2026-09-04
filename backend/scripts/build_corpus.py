"""Process raw documents and build processed_docs/docs.json"""
import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw_docs"
OUT_DIR = BASE_DIR / "data" / "processed_docs"
OUT_FILE = OUT_DIR / "docs.json"


def clean(text: str) -> str:
    text = text.replace("\n", " ")
    return " ".join(text.split())


def build_corpus():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not RAW_DIR.exists():
        print(f"Error: {RAW_DIR} does not exist. Run generate_database_docs.py first.")
        return

    documents = []
    files = sorted([f for f in os.listdir(RAW_DIR) if f.endswith(".txt") and f.startswith("doc_")])

    for idx, filename in enumerate(files):
        path = RAW_DIR / filename
        with open(path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        cleaned_text = clean(raw_text)
        if not cleaned_text:
            continue

        documents.append({
            "id": f"doc_{idx+1:03d}",
            "text": cleaned_text
        })

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(documents)} processed documents to {OUT_FILE}")
    return len(documents)


if __name__ == "__main__":
    build_corpus()
