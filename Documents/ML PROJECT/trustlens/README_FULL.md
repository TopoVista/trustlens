# TrustLens — Full scaffold summary

This file lists the created structure and next steps.

- backend/
  - app/
    - api/
      - routes.py
      - schemas.py
    - pipeline/
      - retriever.py
      - generator.py
      - claims.py
      - verifier.py
      - runner.py
    - models/
      - embeddings.py
      - nli.py
    - utils/
      - text.py
      - io.py
    - main.py
  - data/
    - raw_docs/
    - processed_docs/
    - index.faiss
    - doc_store.json
  - requirements.txt
  - Dockerfile
- frontend/
  - src/
    - components/
    - pages/
    - services/
    - styles/
    - App.jsx
  - public/
  - package.json
  - vercel.json
- docs/
  - architecture.md
  - evaluation.md
  - demo.md

Next steps:
- Implement retrieval and index building
- Add NLI model and evaluation scripts
- Scaffold frontend views and connect to backend
