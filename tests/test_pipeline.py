"""Unit and integration test suite for TrustLens V2"""
import sys
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

# Ensure backend package is in python path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app.pipeline.claims import split_into_claims, normalize_claim
from app.pipeline.retriever import retrieve
from app.pipeline.verifier import verify_single_claim
from app.evaluator.metrics import faithfulness, hallucination_rate, claim_precision, compute_summary_stats
from app.models.nli import verify_claim, verify_claim_batch


client = TestClient(app)


def test_claim_splitting():
    text = (
        "PostgreSQL utilizes Multi-Version Concurrency Control. "
        "B-tree indexes maintain balanced search trees. "
        "Write-ahead logging ensures durability."
    )
    claims = split_into_claims(text)
    assert len(claims) == 3
    assert "PostgreSQL" in claims[0]
    assert "B-tree" in claims[1]
    assert "Write-ahead" in claims[2]


def test_claim_normalization_preserves_uncertainty():
    # Crucial test: modal verbs and hedging must NOT be stripped into false certainty
    hedged = "   This optimization may reduce write amplification in LSM trees.   "
    normalized = normalize_claim(hedged)
    assert "may reduce" in normalized
    assert normalized.startswith("This")
    assert not normalized.endswith(" ")


def test_metrics_empty_safety():
    assert faithfulness([]) == 0.0
    assert hallucination_rate([]) == 0.0
    assert claim_precision([]) == 0.0
    stats = compute_summary_stats([])
    assert stats["claim_count"] == 0
    assert stats["faithfulness"] == 0.0


def test_metrics_calculation():
    sample_claims = [
        {"claim": "C1", "label": "SUPPORTED", "score": 0.90},
        {"claim": "C2", "label": "SUPPORTED", "score": 0.80},
        {"claim": "C3", "label": "NOT_SUPPORTED", "score": 0.40},
        {"claim": "C4", "label": "CONTRADICTED", "score": 0.85},
    ]
    # Faithfulness = (0.90 + 0.80) / 4 = 0.425
    assert round(faithfulness(sample_claims), 3) == 0.425
    # Hallucination rate = 2 / 4 = 0.50
    assert hallucination_rate(sample_claims) == 0.50
    # Precision = 2 / 4 = 0.50
    assert claim_precision(sample_claims) == 0.50


def test_nli_entailment_mapping():
    premise = "B-tree indexes organize keys in sorted order for fast logarithmic lookup."
    hypothesis = "B-tree indexes maintain sorted keys."
    label, score = verify_claim(hypothesis, premise)
    assert label == "entailment"
    assert score > 0.5


def test_api_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "2.0.0"


def test_api_empty_query_rejected():
    response = client.post("/analyze", json={"query": "   ", "k": 5})
    assert response.status_code == 400


@patch("app.api.routes.generate_answer")
def test_api_analyze_with_mocked_llm(mock_generate):
    mock_generate.return_value = (
        "B-tree indexes maintain keys in sorted order. "
        "They eliminate the need for database storage."
    )
    response = client.post("/analyze", json={"query": "How do B-tree indexes work?", "k": 3})
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "answer" in data
    assert "documents" in data
    assert "verified_claims" in data
    assert "stats" in data
    assert len(data["verified_claims"]) >= 2
    assert "faithfulness" in data["stats"]
    assert "retrieval_ms" in data["stats"]
    assert "generation_ms" in data["stats"]


# --- Deterministic sentencizer behavior (replaces spaCy) ---


def test_claim_split_periods():
    text = "First sentence here. Second sentence here. Third sentence here."
    claims = split_into_claims(text)
    assert claims == ["First sentence here.", "Second sentence here.", "Third sentence here."]


def test_claim_split_question_and_exclamation_marks():
    text = "Did the index help? Yes it did! No doubt."
    claims = split_into_claims(text)
    assert claims == ["Did the index help?", "Yes it did!", "No doubt."]


def test_claim_split_abbreviations_do_not_break_sentences():
    text = "The company (e.g. Acme Corp.) is located in the U.S. It ships globally."
    claims = split_into_claims(text)
    assert len(claims) == 2
    assert "U.S." in claims[0]
    assert claims[1] == "It ships globally."


def test_claim_split_decimals_do_not_break_sentences():
    text = "The threshold is 0.70 and the score is 3.5. This is a second sentence."
    claims = split_into_claims(text)
    assert len(claims) == 2
    assert "0.70" in claims[0]


def test_claim_split_newline_separated_claims():
    text = "Claim one about indexes.\nClaim two about transactions.\nClaim three about sharding."
    claims = split_into_claims(text)
    assert len(claims) == 3
    assert claims[0] == "Claim one about indexes."
    assert claims[2] == "Claim three about sharding."


def test_claim_split_bullets_stripped():
    text = "- First bullet claim here.\n- Second bullet claim there.\n"
    claims = split_into_claims(text)
    assert len(claims) == 2
    assert claims[0].startswith("First bullet")
    assert claims[1].startswith("Second bullet")


def test_claim_split_empty_and_short_text():
    assert split_into_claims("") == []
    assert split_into_claims("   \n  \t  ") == []
    assert split_into_claims("Hi.") == []  # shorter than MIN_CLAIM_LEN


# --- NLI deterministic fallback (no OpenAI key in tests) ---


def test_nli_fallback_is_deterministic_and_never_raises(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    pairs = [
        ("B-tree indexes maintain sorted keys", "B-tree indexes organize keys in sorted order."),
        ("The system does not support X", "The system supports X everywhere."),
        ("Totally unrelated topic", "Completely different content here."),
    ]
    results = verify_claim_batch(pairs)
    assert len(results) == len(pairs)
    for label, score in results:
        assert label in {"entailment", "contradiction", "neutral"}
        assert 0.0 <= score <= 1.0


def test_nli_fallback_retrieve_shapes(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    docs = retrieve("B-tree indexes", k=2)
    assert 0 <= len(docs) <= 2
    for d in docs:
        assert set(d.keys()) >= {"id", "text", "score"}
