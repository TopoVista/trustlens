"""Claim extraction and conservative normalization"""
import re
import logging
from typing import List
import spacy

logger = logging.getLogger("trustlens.claims")

_nlp = None


def _load_nlp():
    global _nlp
    if _nlp is None:
        try:
            logger.info("Attempting to load spacy 'en_core_web_sm'...")
            _nlp = spacy.load("en_core_web_sm", disable=["ner", "tagger", "lemmatizer"])
            logger.info("Loaded spacy 'en_core_web_sm'")
        except Exception as e:
            logger.warning("Failed to load 'en_core_web_sm' (%s). Falling back to fast blank English sentencizer.", e)
            _nlp = spacy.blank("en")
            _nlp.add_pipe("sentencizer")
            logger.info("Initialized blank English sentencizer")


def split_into_claims(text: str) -> List[str]:
    """
    Split generated answer text into sentence-level claims using spaCy.
    Handles multi-line text, bullet points, and paragraph breaks.
    """
    if not text or not text.strip():
        return []

    _load_nlp()

    # Pre-clean lines to handle markdown bullet lists nicely
    cleaned_lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Strip markdown bullets like '-', '*', '1.', '2.'
        line = re.sub(r"^(\d+\.|\*|-)\s+", "", line)
        if line:
            cleaned_lines.append(line)

    joined_text = " ".join(cleaned_lines)
    doc = _nlp(joined_text)

    claims = []
    for sent in doc.sents:
        sent_str = sent.text.strip()
        # Remove stray punctuation or non-informative short fragments
        if len(sent_str) >= 5:
            claims.append(sent_str)

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
