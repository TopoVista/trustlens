"""Optional memory diagnostic for the Render Free 512 MB target (Stage 13).

Measures resident set size (RSS) at every critical point of the lightweight
architecture:

    1. Python baseline
    2. `import app.main`
    3. Server startup (FastAPI lifespan via TestClient)
    4. /health
    5. Document ingestion (workspace pipeline)
    6. Workspace knowledge query (full planner: retrieval + claims + NLI + synthesis)
    7. Legacy corpus RAG retrieval (persisted NumPy embeddings)
    8. Claim extraction (regex sentencizer)
    9. Claim verification (OpenAI NLI path)
    10. Grounded answer generation (OpenAI chat path)

The OpenAI client is stubbed so the probe is offline-safe and deterministic;
memory behaviour is identical because no local ML weights are ever loaded.
If psutil is installed it is used for RSS; otherwise the script falls back to
the Windows process API or `resource` (Linux).

Usage:
    cd backend
    python scripts/memory_report.py
"""
import json
import os
import sys
from pathlib import Path

# Give the script access to the backend package
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# The fake key satisfies the "missing OPENAI_API_KEY" guards; no real calls are
# made because the OpenAI client class is stubbed below before any import.
os.environ.setdefault("OPENAI_API_KEY", "sk-memory-probe-fake-key")


# --------------------------------------------------------------------------
# RSS measurement (psutil preferred, graceful fallbacks)
# --------------------------------------------------------------------------
def _get_rss_mb() -> float:
    try:
        import psutil  # type: ignore
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except ImportError:
        pass
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class PMC(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(pmc), pmc.cb):
            return pmc.WorkingSetSize / (1024 * 1024)
        return 0.0
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except Exception:
        return 0.0


# --------------------------------------------------------------------------
# Deterministic OpenAI stub (no network, no local ML)
# --------------------------------------------------------------------------
def _install_fake_openai() -> None:
    import openai

    nli_results = [
        {"index": i, "label": "entailment" if i % 3 == 0 else ("contradiction" if i % 3 == 1 else "neutral"),
         "confidence": 0.86}
        for i in range(20)
    ]
    fake_json = json.dumps({
        "results": nli_results,
        "answer": "Stubbed grounded answer confirming the documented facts.",
        "confidence": 0.87,
        "claims": [], "evidence": [], "contradictions": [],
        "assumptions": [], "unknowns": [], "related_knowledge": {},
    })

    class _Data:
        def __init__(self, dim):
            self.embedding = [0.001 * ((i % 7) - 3) for i in range(dim)]

    class _Embeddings:
        def create(self, model=None, input=None, **kwargs):
            class _Resp:
                data = [_Data(1536) for _ in input]
            return _Resp()

    class _Message:
        content = fake_json

    class _Choice:
        message = _Message()

    class _Completion:
        choices = [_Choice()]

    class _Completions:
        def create(self, **kwargs):
            return _Completion()

    class _Chat:
        completions = _Completions()

    class _FakeOpenAI:
        def __init__(self, **kwargs):
            self.embeddings = _Embeddings()
            self.chat = _Chat()

    openai.OpenAI = _FakeOpenAI


_install_fake_openai()

report = []


def record(step):
    mb = _get_rss_mb()
    report.append((step, mb))
    print(f"{step:<58} RSS: {mb:7.1f} MB")

def main() -> int:
    print("=" * 76)
    print("TrustLens memory diagnostic (Render Free 512 MB target)")
    print("=" * 76)

    record("1. Python baseline")

    import app.main  # noqa: E402
    # app.main loads backend/.env with override=True, which may wipe or empty
    # the fake key; restore it so stubbed OpenAI paths construct clients.
    os.environ["OPENAI_API_KEY"] = "sk-memory-probe-fake-key"
    record("2. import app.main (module import complete)")

    from fastapi.testclient import TestClient  # noqa: E402
    record("2b. fastapi.testclient imported")

    with TestClient(app.main.app) as client:
        record("3. Server startup (FastAPI lifespan executed)")

        r = client.get("/health")
        assert r.status_code == 200, r.text
        record("4. GET /health -> 200")

        doc_payload = {
            "title": "Vendor Security Overview",
            "raw_content": (
                "Acme Cloud encrypts all data at rest with AES-256. "
                "The platform is SOC 2 Type II certified since 2023. "
                "Data is replicated across three availability zones. "
                "Breaches are reported within 72 hours per GDPR! "
                "Is customer data isolated per tenant? "
                "U.S. Dept. of Defense reviewed the architecture. "
                "The vendor does not support customer-managed keys."
            ),
        }
        r = client.get(
            "/api/workspaces",
            headers={"x-user-id": "memory_probe_user"},
        )
        assert r.status_code == 200 and r.json(), r.text
        workspace_id = r.json()[0]["id"]

        r = client.post(
            f"/api/workspaces/{workspace_id}/documents",
            json=doc_payload,
            headers={"x-user-id": "memory_probe_user"},
        )
        assert r.status_code == 200, r.text
        doc_res = r.json()
        record(f"5. POST documents (ingestion: {doc_res.get('chunks_count')} chunks, "
               f"{doc_res.get('claims_extracted')} claims)")

        r = client.get(
            f"/api/workspaces/{workspace_id}/claims",
            headers={"x-user-id": "memory_probe_user"},
        )
        assert r.status_code == 200, r.text
        record(f"6. GET claims ({len(r.json())} claims returned)")

        r = client.post(
            f"/api/workspaces/{workspace_id}/query",
            json={"query": "How is data encrypted and isolated?"},
            headers={"x-user-id": "memory_probe_user"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        record(f"7. POST workspace query (intent={body.get('intent')}, "
               f"{len(body.get('evidence', []))} evidence, {len(body.get('claims', []))} claims)")

        from app.pipeline import retriever
        docs = retriever.retrieve("cloud data encryption at rest", k=5)
        assert docs, "legacy corpus retrieval returned nothing"
        record(f"8. Legacy RAG retrieval (top score {docs[0]['score']})")

        from app.pipeline import claims
        sentences = claims.split_into_claims(
            "The vendor is SOC 2 certified. Data is encrypted! "
            "Is it isolated? Mr. Smith confirmed it.\nNewline claim."
        )
        record(f"9. Claim extraction ({len(sentences)} sentences)")

        from app.models import nli
        verdicts = nli.verify_claim_batch([
            ("Data is encrypted at rest.", "All data at rest is encrypted with AES-256."),
            ("The vendor supports customer-managed keys.", "The vendor does not support customer-managed keys."),
        ])
        record(f"10. Claim verification (NLI: {verdicts[0][0]} / {verdicts[1][0]})")

        from app.pipeline import generator
        answer = generator.generate_answer(
            "How is data encrypted?", [{"id": "d1", "text": "AES-256 at rest."}]
        )
        assert answer
        record("11. Grounded answer generation")

    # Heavy-module import check
    heavy = [m for m in ("torch", "transformers", "sentence_transformers", "faiss", "spacy")
             if m in sys.modules]
    peak = max(mb for _, mb in report)
    idle = report[1][1]  # after import app.main

    print("-" * 76)
    print(f"PEAK RSS observed:              {peak:7.1f} MB")
    print(f"IDLE RSS (after import):        {idle:7.1f} MB")
    print(f"Heavy modules in sys.modules:   {heavy if heavy else 'NONE'}")
    print("-" * 76)

    ok = peak < 512.0
    warn = "" if idle < 150 else "  (target <150 MB idle not met - investigate)"
    print(f"RESULT: {'PASS' if ok else 'FAIL'} - peak must stay below 512 MB.{warn}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())