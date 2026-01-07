"""NLI model wrapper (lazy-loaded, memory-safe)"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Tuple

_MODEL_NAME = "roberta-large-mnli"

_tokenizer = None
_model = None


def _get_model():
    global _tokenizer, _model

    if _model is None or _tokenizer is None:
        print("⏳ Lazy-loading NLI model...")

        _tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
        _model = AutoModelForSequenceClassification.from_pretrained(_MODEL_NAME)

        _model.eval()

        print("✅ NLI model loaded.")

    return _tokenizer, _model


def verify_claim(claim: str, evidence: str) -> Tuple[str, float]:
    """
    Verify a claim against a single piece of evidence.

    Returns:
        (label, confidence)
        label ∈ {"entailment", "contradiction", "neutral"}
    """

    tokenizer, model = _get_model()

    inputs = tokenizer(
        evidence,
        claim,
        return_tensors="pt",
        truncation=True,
        padding=True
    )

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=1)[0]

    labels = ["contradiction", "neutral", "entailment"]

    idx = torch.argmax(probs).item()
    return labels[idx], probs[idx].item()
