"""NLI model wrapper (lazy-loaded, memory-safe, dynamic label mapping, batch-capable)"""
import os
import logging
from typing import Tuple, List, Dict
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger("trustlens.nli")

_DEFAULT_MODEL = "cross-encoder/nli-MiniLM2-L6-H768"

_tokenizer = None
_model = None
_id2label_map: Dict[int, str] = {}


def _get_model():
    global _tokenizer, _model, _id2label_map

    if _model is None or _tokenizer is None:
        model_name = os.getenv("NLI_MODEL", _DEFAULT_MODEL).strip()
        hf_token = os.getenv("HF_TOKEN") or False

        logger.info("⏳ Lazy-loading NLI model: %s...", model_name)
        try:
            _tokenizer = AutoTokenizer.from_pretrained(model_name, token=hf_token)
            _model = AutoModelForSequenceClassification.from_pretrained(model_name, token=hf_token)
            _model.eval()

            # Dynamically extract and normalize id2label mapping from model configuration
            raw_id2label = getattr(_model.config, "id2label", {})
            _id2label_map = {}
            for idx, raw_label in raw_id2label.items():
                label_str = str(raw_label).lower().strip()
                if "entail" in label_str:
                    _id2label_map[int(idx)] = "entailment"
                elif "contra" in label_str:
                    _id2label_map[int(idx)] = "contradiction"
                else:
                    _id2label_map[int(idx)] = "neutral"

            logger.info("✅ NLI model loaded successfully. Dynamic label mapping: %s", _id2label_map)

        except Exception as e:
            logger.error("Failed to load NLI model '%s': %s", model_name, e)
            raise RuntimeError(
                f"Failed to initialize NLI model '{model_name}'. "
                "Please verify internet access or model availability."
            ) from e

    return _tokenizer, _model, _id2label_map


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
    Verify a batch of (claim, evidence) pairs efficiently.
    Returns list of (label, confidence).
    """
    if not pairs:
        return []

    tokenizer, model, id2label = _get_model()

    # In standard NLI, premise comes first (evidence) and hypothesis comes second (claim)
    premises = [p[1] for p in pairs]
    hypotheses = [p[0] for p in pairs]

    inputs = tokenizer(
        premises,
        hypotheses,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512
    )

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probabilities = torch.softmax(logits, dim=1)

    results = []
    for probs in probabilities:
        best_idx = torch.argmax(probs).item()
        best_label = id2label.get(best_idx, "neutral")
        confidence = float(probs[best_idx].item())
        results.append((best_label, confidence))

    return results
