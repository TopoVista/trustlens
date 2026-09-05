"""NLI claim verification via OpenAI API with deterministic fallback (no torch).

Public interface preserved:

- ``verify_claim(claim, evidence)`` -> ``(label, confidence)``
- ``verify_claim_batch(pairs)`` -> ``List[(label, confidence)]``

Labels use the exact same vocabulary as the previous cross-encoder wrapper:
``"entailment"``, ``"contradiction"``, ``"neutral"``.

Strategy:
  * Primary: OpenAI chat completions with structured JSON output classifying
    premise/hypothesis pairs as entailment / contradiction / neutral.
  * Deterministic fallback: lexical overlap + negation/numeric heuristics so a
    transient OpenAI failure or missing API key never crashes verification.
"""
import json
import logging
import os
import re
from typing import List, Optional, Tuple

from openai import OpenAI

logger = logging.getLogger("trustlens.nli")

_DEFAULT_OPENAI_NLI_MODEL = "gpt-4o-mini"
_BATCH_SIZE = 20  # pairs per OpenAI request


def _normalize_label(raw) -> str:
    label = str(raw or "").lower().strip()
    if "entail" in label:
        return "entailment"
    if "contra" in label:
        return "contradiction"
    return "neutral"


def _get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY", "").strip().strip("\"'")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is missing.")
    return OpenAI(api_key=api_key)


def _verify_batch_openai(pairs: List[Tuple[str, str]]) -> Optional[List[Tuple[str, float]]]:
    """Classify (hypothesis, premise) pairs via OpenAI JSON output.

    Each pair is ``(claim, evidence)``; in NLI terms the evidence is the
    premise and the claim is the hypothesis. Returns ``None`` on any failure so
    the caller can use the deterministic fallback instead.
    """
    client = _get_openai_client()
    model = os.getenv("OPENAI_NLI_MODEL", _DEFAULT_OPENAI_NLI_MODEL).strip() or _DEFAULT_OPENAI_NLI_MODEL
    results: List[Tuple[str, float]] = []

    for start in range(0, len(pairs), _BATCH_SIZE):
        batch = pairs[start:start + _BATCH_SIZE]
        lines = []
        for idx, (claim, evidence) in enumerate(batch):
            lines.append(
                "{i}: PREMISE: {p}\nHYPOTHESIS: {h}".format(
                    i=idx,
                    p=(evidence or "").strip()[:1500],
                    h=(claim or "").strip()[:1500],
                )
            )

        system_prompt = (
            "You are a precise natural language inference (NLI) classifier. "
            "Determine whether each HYPOTHESIS is entailed by, contradicted by, "
            "or neutral with respect to its PREMISE."
        )
        user_prompt = (
            "Classify each numbered PREMISE/HYPOTHESIS pair. "
            "Each label must be exactly one of: entailment, contradiction, neutral. "
            "Return ONLY a JSON object with a top-level key \"results\" whose value is "
            "an array of objects with fields: index (int), label (string), confidence "
            "(float between 0 and 1).\n\n"
            + "\n\n".join(lines)
        )

        try:
            response = client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
                max_tokens=500,
            )
            content = response.choices[0].message.content or "{}"
            payload = json.loads(content)
        except Exception as e:  # noqa: BLE001 - fall back deterministically
            logger.warning("OpenAI NLI batch failed (%s); using deterministic fallback.", e)
            return None

        items = payload.get("results")
        if not isinstance(items, list):
            logger.warning("OpenAI NLI returned unexpected shape; using deterministic fallback.")
            return None

        batch_results: List[Optional[Tuple[str, float]]] = [None] * len(batch)
        for item in items:
            try:
                idx = int(item.get("index", -1))
                label = _normalize_label(item.get("label"))
                confidence = max(0.0, min(1.0, float(item.get("confidence", 0.5))))
            except (TypeError, ValueError):
                continue
            if 0 <= idx < len(batch):
                batch_results[idx] = (label, confidence)

        for row in batch_results:
            if row is None:
                logger.warning("OpenAI NLI batch incomplete; using deterministic fallback.")
                return None
            results.append(row)

    return results


def _token_set(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _fallback_verify(claim: str, evidence: str) -> Tuple[str, float]:
    """Deterministic lexical NLI fallback used when OpenAI is unavailable.

    Uses token overlap between the claim (hypothesis) and evidence (premise),
    negation polarity, and numeric conflicts to approximate the original
    cross-encoder verdicts.
    """
    claim_tokens = _token_set(claim)
    evidence_tokens = _token_set(evidence)
    if not claim_tokens:
        return ("neutral", 0.5)

    overlap = len(claim_tokens & evidence_tokens) / float(len(claim_tokens))

    neg_words = {
        "not", "never", "no", "cannot", "can't", "couldn't", "doesn't", "didn't",
        "isn't", "aren't", "without", "fails", "fail", "failed", "denied", "deny",
        "prohibited", "prohibit", "against", "contradict", "contradicts", "but",
    }
    claim_neg = claim_tokens & neg_words
    evidence_neg = evidence_tokens & neg_words

    claim_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", (claim or "").lower()))
    evidence_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", (evidence or "").lower()))
    numeric_conflict = bool(
        overlap >= 0.4
        and claim_numbers
        and evidence_numbers
        and claim_numbers.isdisjoint(evidence_numbers)
    )

    if overlap >= 0.4 and claim_neg and not (claim_neg & evidence_neg):
        return ("contradiction", round(0.65 + 0.25 * overlap, 3))
    if numeric_conflict:
        return ("contradiction", round(0.6 + 0.25 * overlap, 3))
    if overlap >= 0.6:
        return ("entailment", round(0.6 + 0.38 * overlap, 3))
    if overlap >= 0.25:
        return ("neutral", round(0.45 + 0.2 * overlap, 3))
    return ("neutral", round(max(0.05, overlap), 3))


def verify_claim(claim: str, evidence: str) -> Tuple[str, float]:
    """
    Verify a claim against a single piece of evidence.
    Returns:
        (label, confidence) where label in {"entailment", "contradiction", "neutral"}
    """
    results = verify_claim_batch([(claim, evidence)])
    return results[0]


def verify_claim_batch(pairs: List[Tuple[str, str]]) -> List[Tuple[str, float]]:
    """
    Verify a batch of (claim, evidence) pairs.
    Returns a list of (label, confidence) tuples matching the input order.

    Never raises: OpenAI failures degrade to the deterministic fallback.
    """
    if not pairs:
        return []

    try:
        openai_results = _verify_batch_openai(pairs)
        if openai_results is not None and len(openai_results) == len(pairs):
            return openai_results
    except Exception as e:  # noqa: BLE001 - never crash the application
        logger.warning("OpenAI NLI unavailable (%s); using deterministic fallback.", e)

    return [_fallback_verify(claim, evidence) for (claim, evidence) in pairs]
