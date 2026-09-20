"""Unit and integration test suite for TrustLens V2"""
import sys
from pathlib import Path

# Ensure backend package is in python path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.pipeline.claims import split_into_claims, normalize_claim
from app.models.nli import verify_claim, verify_claim_batch


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


def test_nli_entailment_mapping():
    premise = "B-tree indexes organize keys in sorted order for fast logarithmic lookup."
    hypothesis = "B-tree indexes maintain sorted keys."
    label, score = verify_claim(hypothesis, premise)
    assert label == "entailment"
    assert score > 0.5


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

