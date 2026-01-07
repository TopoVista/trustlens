import spacy
import re
from typing import List

_nlp = None


def _load_nlp():
    global _nlp
    if _nlp is None:
        print("⏳ Loading spaCy model...")
        _nlp = spacy.load("en_core_web_sm", disable=["ner", "tagger"])
        print("✅ spaCy model loaded.")


def split_into_claims(text: str) -> List[str]:
    _load_nlp()

    doc = _nlp(text)

    claims = []
    for sent in doc.sents:
        claim = sent.text.strip()
        if claim:
            claims.append(claim)

    return claims


# ---------------- DAY 15: NORMALIZATION ---------------- #

MODAL_VERBS = [
    r"\bcan\b",
    r"\bmay\b",
    r"\bmight\b",
    r"\bcould\b",
    r"\bwould\b",
    r"\bshould\b"
]

HEDGING_PHRASES = [
    r"\btypically\b",
    r"\bgenerally\b",
    r"\boften\b",
    r"\busually\b",
    r"\bwidely\b",
    r"\bcommonly\b",
    r"\bseems to\b",
    r"\bappears to\b"
]


def normalize_claim(claim: str) -> str:
    normalized = claim.lower()

    for pattern in MODAL_VERBS:
        normalized = re.sub(pattern, "", normalized)

    for pattern in HEDGING_PHRASES:
        normalized = re.sub(pattern, "", normalized)

    # Cleanup extra spaces
    normalized = re.sub(r"\s+", " ", normalized).strip()

    # Capitalize first letter for readability
    if normalized:
        normalized = normalized[0].upper() + normalized[1:]

    return normalized
