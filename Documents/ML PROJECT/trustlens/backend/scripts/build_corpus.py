import os
import json
from backend.app.utils.text import clean

RAW_DIR = "backend/data/raw_docs"
OUT_FILE = "backend/data/processed_docs/docs.json"

documents = []

for idx, filename in enumerate(sorted(os.listdir(RAW_DIR))):
    if not filename.endswith(".txt"):
        continue

    path = os.path.join(RAW_DIR, filename)

    with open(path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    cleaned_text = clean(raw_text)

    if len(cleaned_text) == 0:
        continue

    documents.append({
        "id": f"doc_{idx:03d}",
        "text": cleaned_text
    })

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(documents, f, indent=2, ensure_ascii=False)

print(f"Saved {len(documents)} documents to {OUT_FILE}")
