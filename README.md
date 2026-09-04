# TrustLens V2 — AI Reliability & RAG Claim Verification

> **“RAG retrieves evidence for generation; TrustLens independently retrieves evidence to verify what the model actually said.”**

TrustLens is an AI reliability and claim verification platform designed to catch hallucinations and ground LLM outputs. Rather than trusting a generated answer at face value, TrustLens deconstructs the response into sentence-level claims, independently retrieves evidence for each claim, and evaluates grounding using Natural Language Inference (NLI).

---

## Architecture

```
                                USER QUERY
                                    │
                                    ▼
                          ┌──────────────────┐
                          │ MiniLM-L6 Embed  │
                          └─────────┬────────┘
                                    │
                                    ▼
                          ┌──────────────────┐
                          │  FAISS Retrieval │  (Cosine Inner-Product)
                          └─────────┬────────┘
                                    │ Top-5 Evidence
                                    ▼
                          ┌──────────────────┐
                          │ OpenAI Generation│  (Strictly Grounded Prompt)
                          └─────────┬────────┘
                                    │
                                    ▼
                          ┌──────────────────┐
                          │ spaCy Claim Split│  (Sentence Decomposition)
                          └─────────┬────────┘
                                    │ Atomic Claims
                                    ▼
                          ┌──────────────────┐
                          │ Claim Retrieval  │  (Independent Top-3 FAISS Search)
                          └─────────┬────────┘
                                    │ Claim-Evidence Pairs
                                    ▼
                          ┌──────────────────┐
                          │ MiniLM2-L6 NLI   │  (Premise-Hypothesis Classification)
                          └─────────┬────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 ▼                  ▼                  ▼
          [ SUPPORTED ]     [ NOT_SUPPORTED ]   [ CONTRADICTED ]
          (Entailment ≥0.70) (Insufficient Data) (Contradiction ≥0.70)
                 │                  │                  │
                 └──────────────────┼──────────────────┘
                                    ▼
                          ┌──────────────────┐
                          │   Trust Report   │  (Faithfulness Score + Evidence Cards)
                          └──────────────────┘
```

---

## Tech Stack

- **Frontend**: React 18, Vite 5, Tailwind CSS, Framer Motion, Lucide React
- **Backend API**: FastAPI, Uvicorn, Pydantic v2, Python Dotenv
- **Vector Retrieval**: FAISS (`IndexFlatIP`), `sentence-transformers/all-MiniLM-L6-v2`
- **Generation**: OpenAI Python SDK (`gpt-5.6-luna` / configurable)
- **Claim Decomposition**: spaCy sentence segmentation with robust blank-sentencizer fallback
- **Verification Engine**: Hugging Face Transformers, `cross-encoder/nli-MiniLM2-L6-H768`, PyTorch
- **Corpus**: 450 technical database architecture and internals documents
- **Deployment**: Render (FastAPI Web Service) + Vercel (Vite React SPA)

---

## End-to-End Workflow

1. **Query Ingestion**: The user submits a technical query (e.g., *"Why do B-tree indexes improve query performance?"*).
2. **Context Retrieval**: The query is embedded via `all-MiniLM-L6-v2` and searched against FAISS vector storage to pull top-$k$ documents.
3. **Grounded Synthesis**: OpenAI receives the query and retrieved context under strict instructions: *use only provided documents, do not speculate, acknowledge missing facts*.
4. **Sentence Decomposition**: The generated answer is decomposed into individual verifiable claims using spaCy.
5. **Independent Claim Retrieval**: For each extracted claim, TrustLens performs a fresh, targeted vector retrieval against the corpus.
6. **NLI Verification**: Each (evidence premise, claim hypothesis) pair is evaluated by `cross-encoder/nli-MiniLM2-L6-H768` with dynamic label mapping:
   - **Contradiction $\ge 0.70$** $\rightarrow$ `CONTRADICTED`
   - **Entailment $\ge 0.70$** $\rightarrow$ `SUPPORTED`
   - **Else** $\rightarrow$ `NOT_SUPPORTED` (insufficient evidence)
7. **Faithfulness Scoring & Telemetry**: Faithfulness is computed as the confidence-weighted entailment ratio across all claims. Latency profiling tracks retrieval, generation, and verification milliseconds.

---

## Local Development Setup

### Prerequisites
- Python 3.12+ (or 3.13)
- Node.js 18+ and npm
- OpenAI API Key

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure OpenAI key
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY

# Start backend server
uvicorn app.main:app --reload --port 8000
```

Verify backend health at: [http://localhost:8000/health](http://localhost:8000/health)

### 2. Frontend Setup

```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env
# Ensure VITE_API_URL=http://localhost:8000

# Start Vite development server
npm run dev
```

Open your browser at [http://localhost:5173](http://localhost:5173).

---

## Environment Variables

### Backend (`backend/.env`)

```ini
# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.6-luna

# CORS Allowed Origins (comma-separated)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Verification & Retrieval Settings
NLI_MODEL=cross-encoder/nli-MiniLM2-L6-H768
NLI_THRESHOLD=0.70
RETRIEVAL_K=5
CLAIM_RETRIEVAL_K=3
```

### Frontend (`frontend/.env`)

```ini
VITE_API_URL=http://localhost:8000
```

---

## Production Deployment

### 1. Backend Deployment to Render

1. Create a new **Web Service** on [Render.com](https://render.com).
2. Connect your GitHub repository.
3. Configure settings:
   - **Name**: `trustlens-api`
   - **Environment**: `Python 3`
   - **Root Directory**: *(leave blank or `.`)*
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
4. Add Environment Variables in the Render Dashboard:
   - `OPENAI_API_KEY`: *(your real OpenAI secret key)*
   - `OPENAI_MODEL`: `gpt-5.6-luna`
   - `CORS_ORIGINS`: `https://YOUR-VERCEL-DOMAIN.vercel.app`
   - `NLI_MODEL`: `cross-encoder/nli-MiniLM2-L6-H768`
   - `NLI_THRESHOLD`: `0.70`
   - `RETRIEVAL_K`: `5`
   - `CLAIM_RETRIEVAL_K`: `3`
5. Deploy and copy your Render live service URL (e.g., `https://trustlens-api.onrender.com`).

*(Note: `render.yaml` is also included at the project root for automated Render Blueprint deployments.)*

### 2. Frontend Deployment to Vercel

1. Import your repository into [Vercel](https://vercel.com).
2. Set **Root Directory** to `frontend`.
3. Framework Preset will automatically detect **Vite**.
4. Configure Build and Output settings:
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Add Environment Variable:
   - `VITE_API_URL`: `https://YOUR-RENDER-SERVICE.onrender.com` *(your live Render backend URL without trailing slash)*
6. Deploy!

---

## Running Automated Tests

A comprehensive pytest suite validates retrieval, claim splitting, uncertainty preservation, NLI entailment mapping, and API endpoints with mocked LLM calls:

```bash
# Run test suite from repository root
pytest tests/ -v
```

Tests run completely offline without requiring an active `OPENAI_API_KEY`.

---

## Important Semantic Distinction

> **`NOT_SUPPORTED` does NOT mean `FALSE`.**

A verdict of `NOT_SUPPORTED` indicates that the specific evidence retrieved from the corpus was insufficient to conclusively prove the claim. It protects users from blind trust without falsely asserting that the LLM stated an objective falsehood. `CONTRADICTED` is reserved for claims directly refuted by retrieved evidence.

---

## Limitations

1. **Corpus Coverage**: TrustLens can only ground claims present in its database corpus (450 documents on database internals). Queries on outside topics will yield `NOT_SUPPORTED`.
2. **Atomic Splitting**: Complex compound sentences with dependent clauses are split at sentence boundaries. Very dense sentences with mixed factual accuracy are evaluated as a whole.
3. **NLI Threshold Sensitivity**: Highly subtle entailments may fall below the 0.70 confidence threshold and default to `NOT_SUPPORTED`.

---

## Future Roadmap

- **Hybrid Retrieval**: Combine dense semantic FAISS embeddings with sparse BM25 keyword matching for exact numerical and identifier queries.
- **Span-Level Evidence Attribution**: Highlight precise character offsets and token spans within evidence documents rather than document-level excerpts.
- **Sub-Sentence Clause Parsing**: Deconstruct compound sentences into atomic fact triplets $(subject, predicate, object)$ for finer-grained verification.
- **Cross-Encoder Reranking**: Add a BGE or Cohere reranker prior to generation to maximize evidence precision.
- **Verification Feedback Loop**: Automatically prompt the generator to revise or redact ungrounded claims before presenting the final verified response to the user.
