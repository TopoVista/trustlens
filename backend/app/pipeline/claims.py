"""Claim extraction and conservative normalization (deterministic, no spaCy).

Sentence splitting is implemented with a lightweight regex sentencizer that
handles terminal punctuation (``.`` ``!`` ``?``), common abbreviations,
currency/statistics decimals, and newline-separated claims while preserving the
previous spaCy-based pipeline's output shape.
"""
import re
import logging
from typing import List

logger = logging.getLogger("trustlens.claims")

# Minimum meaningful claim length (kept identical to previous pipeline).
_MIN_CLAIM_LEN = 5

# Abbreviations whose trailing period must NOT terminate a sentence.
# Sorted longest-first so "u.s." outranks "u." etc.
_ABBREVIATIONS = sorted({
    "mr.", "mrs.", "ms.", "dr.", "prof.", "sr.", "jr.", "st.", "vs.", "etc.",
    "e.g.", "i.e.", "cf.", "al.", "inc.", "ltd.", "corp.", "co.", "dept.",
    "approx.", "est.", "fig.", "no.", "vol.", "ed.", "eds.", "jan.", "feb.",
    "mar.", "apr.", "jun.", "jul.", "aug.", "sep.", "sept.", "oct.", "nov.",
    "dec.", "u.s.", "u.k.", "u.s.a.",
}, key=len, reverse=True)

_ABBR_PLACEHOLDER = "\x00"


def _protect_abbreviations(text: str) -> str:
    """Temporarily hide periods in abbreviations to prevent false splits."""
    for abbr in _ABBREVIATIONS:
        text = text.replace(abbr, abbr.replace(".", _ABBR_PLACEHOLDER))
    return text


def _restore_abbreviations(text: str) -> str:
    return text.replace(_ABBR_PLACEHOLDER, ".")


def _split_sentences(text: str) -> List[str]:
    """Split a single logical line into sentences on terminal punctuation.

    The lookbehind ``(?<=[.!?])`` combined with the whitespace requirement
    means decimals such as ``0.70`` or ``3.5%`` are never split, and protected
    abbreviations are never treated as sentence boundaries.
    """
    if not text or not text.strip():
        return []
    protected = _protect_abbreviations(text.strip())
    parts = re.split(r"(?<=[.!?])\s+", protected)
    return [_restore_abbreviations(p) for p in parts if p.strip()]


def split_into_claims(text: str) -> List[str]:
    """
    Split generated answer text into sentence-level claims.

    Behaves like the previous spaCy sentencizer pipeline:
    - strips markdown bullet markers from each line (e.g. "- ", "* ", "1. ")
    - treats newlines and terminal punctuation as claim boundaries
    - ignores empty fragments and fragments shorter than 5 characters
    """
    if not text or not text.strip():
        return []

    claims: List[str] = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Strip markdown bullets like '-', '*', '1.', '2.'
        line = re.sub(r"^(\d+\.|\*|-)\s+", "", line)

        for sentence in _split_sentences(line):
            sentence = sentence.strip()
            if len(sentence) >= _MIN_CLAIM_LEN:
                claims.append(sentence)

    return claims


def normalize_claim(claim: str) -> str:
    """
    Conservatively normalize claim for retrieval and NLI matching.
    Crucially preserves semantic hedging and modal verbs (e.g. 'can', 'may', 'might')
    to prevent artificially transforming uncertain statements into absolute claims.
    """
    if not claim:
        return ""

    # Remove leading list markers or quotes
    normalized = re.sub(r"^[\s\"'•\-\*]+", "", claim)
    normalized = re.sub(r"[\"']+$", "", normalized)

    # Collapse multiple whitespaces into a single space
    normalized = re.sub(r"\s+", " ", normalized).strip()

    # Ensure clean capital starting letter
    if normalized:
        normalized = normalized[0].upper() + normalized[1:]

    return normalized
