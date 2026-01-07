"""NLI model wrapper"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Tuple

_MODEL_NAME = "roberta-large-mnli"

_tokenizer = None
_model = None


def _load_model():
    global _tokenizer, _model

    if _tokenizer is None or _model is None:
        print("⏳ Loading NLI model...")
        _tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
        _model = AutoModelForSequenceClassification.from_pretrained(_MODEL_NAME)
        _model.eval()
        print("✅ NLI model loaded.")


def verify_claim(claim: str, evidence: str) -> Tuple[str, float]:
    """
    Verify a claim against a single piece of evidence.

    Returns:
        (label, confidence)
        label ∈ {"entailment", "contradiction", "neutral"}
    """
    _load_model()

    inputs = _tokenizer(
        evidence,
        claim,
        return_tensors="pt",
        truncation=True,
        padding=True
    )

    with torch.no_grad():
        outputs = _model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=1)[0]

    # Label mapping for MNLI models
    labels = ["contradiction", "neutral", "entailment"]

    max_idx = torch.argmax(probs).item()
    label = labels[max_idx]
    confidence = probs[max_idx].item()

    return label, confidence
