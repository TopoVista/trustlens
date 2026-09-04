# TrustLens Error Analysis

## Overview

This document analyzes systematic errors observed in TrustLens during evaluation
and ablation studies. The goal is to understand not only *what* failed,
but *why* these failures occur and how they could be addressed in future iterations.

---

## Error Category 1: Overly Strict Claim Normalization

### Description

Claim normalization removes modal verbs and hedging language to make claims
explicitly verifiable. However, this can unintentionally strengthen claims
beyond what the evidence supports.

### Example

Original sentence:
> “B-tree indexes typically improve performance.”

Normalized claim:
> “B-tree indexes improve performance.”

Verification result:
- Marked as **CONTRADICTED** or **NOT_SUPPORTED**

### Root Cause

Normalization removes uncertainty markers, converting probabilistic statements
into absolute claims. Evidence that discusses trade-offs or conditional benefits
may then contradict the strengthened claim.

### Impact

- Increases false contradictions
- Penalizes nuanced but correct statements

### Possible Mitigations

- Preserve modality as metadata instead of deleting it
- Introduce graded claim strength (e.g., weak vs strong claims)
- Verify claims under multiple normalization variants

---

## Error Category 2: Corpus Coverage Gaps

### Description

TrustLens relies on explicit evidence in the corpus. Claims that are commonly
known but not explicitly documented are marked as unsupported.

### Example

Claim:
> “ACID properties ensure transaction reliability.”

Result:
- **NOT_SUPPORTED**

### Root Cause

The corpus lacks a direct definition sentence covering this claim.

### Impact

- False negatives for common-knowledge facts
- High hallucination rates for definition-style queries

### Possible Mitigations

- Expand corpus coverage
- Add reference documents for foundational concepts
- Use curated background knowledge sources

---

## Error Category 3: NLI Model Misinterpretation of Trade-offs

### Description

The NLI model sometimes interprets trade-off discussions as contradictions,
even when they do not directly negate a claim.

### Example

Evidence:
> “B-tree indexes trade off write performance for faster reads.”

Claim:
> “B-tree indexes improve performance.”

Result:
- **CONTRADICTED**

### Root Cause

The MNLI model treats performance trade-offs as contradictory to blanket claims,
even when the claim is conditionally true.

### Impact

- Over-detection of contradictions
- Conservative verification behavior

### Possible Mitigations

- Aggregate multiple evidence sources before labeling contradiction
- Require stronger contradiction confidence thresholds
- Use domain-adapted NLI models

---

## Error Category 4: Claim Granularity Limitations

### Description

Sentence-level claim splitting does not fully decompose compound factual assertions.

### Example

Sentence:
> “Indexes improve performance and preserve transactional guarantees.”

Treated as:
- One claim instead of two atomic claims

### Root Cause

Claim splitting operates at the sentence level rather than clause level.

### Impact

- Partial support or contradiction is hidden
- Verification signal is less precise

### Possible Mitigations

- Clause-level claim extraction using dependency parsing
- Semantic role labeling for finer decomposition

---

## Error Category 5: Pronoun and Coreference Issues

### Description

Claims containing pronouns lack explicit referents, weakening verification.

### Example

Claim:
> “They are widely used in modern databases.”

Result:
- **NOT_SUPPORTED**

### Root Cause

The verifier does not resolve “they” to a concrete entity.

### Impact

- Legitimate claims fail verification
- Increased NOT_SUPPORTED rate

### Possible Mitigations

- Add coreference resolution before verification
- Rewrite claims with explicit subjects

---

## Summary of Error Patterns

| Error Type | Effect |
|----------|--------|
| Over-normalization | False contradictions |
| Corpus gaps | False unsupported claims |
| NLI trade-off bias | Over-conservative labels |
| Coarse claim splitting | Hidden partial errors |
| No coreference resolution | Weak verification |

---

## Conclusion

TrustLens errs conservatively by design, preferring to abstain or contradict
rather than hallucinate support. While this leads to false negatives in some cases,
it aligns with the system’s goal of exposing ungrounded claims.

These errors highlight clear directions for future work, including improved
claim modeling, richer corpora, and domain-adapted verification models.
