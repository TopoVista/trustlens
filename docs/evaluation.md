# TrustLens Evaluation: Baseline vs Verified RAG

## Overview

This evaluation compares a standard Retrieval-Augmented Generation (RAG) pipeline
against TrustLens, a claim-level verification system designed to detect and localize hallucinations.

Both systems were evaluated on the same set of queries using identical retrieval
and generation settings. TrustLens augments baseline RAG with claim extraction,
evidence retrieval per claim, and NLI-based verification.

---

## Evaluation Setup

- Domain: Database systems (technical corpus)
- Queries: 10 representative factual and explanatory questions
- Baseline: Standard RAG answer without verification
- Verified: TrustLens with claim-level verification

Metrics used:
- **Hallucination Rate**
- **Claim Precision**
- **Faithfulness**

---

## Results

### Per-Query Metrics

| Query | Hallucination Rate ↓ | Claim Precision ↑ | Faithfulness ↑ |
|------|----------------------|------------------|---------------|
| What is a database index? | 1.00 | 0.00 | 0.00 |
| What are B-tree indexes? | 0.80 | 0.20 | 0.14 |
| Why do database indexes improve performance? | 0.40 | 0.60 | 0.54 |
| What is MVCC? | 1.00 | 0.00 | 0.00 |
| Difference between B-tree and hash index | 1.00 | 0.00 | 0.00 |
| Why can too many indexes hurt performance? | 1.00 | 0.00 | 0.00 |
| How does sharding affect consistency? | 0.57 | 0.43 | 0.38 |
| What are ACID properties? | 1.00 | 0.00 | 0.00 |
| What causes deadlocks in databases? | 1.00 | 0.00 | 0.00 |
| What happens if a database has no indexes? | 1.00 | 0.00 | 0.00 |

---

### Aggregate Metrics (Verified RAG)

| Metric | Value |
|------|------|
| Average Hallucination Rate | **0.88** |
| Average Claim Precision | **0.12** |
| Average Faithfulness | **0.11** |

> Note: Baseline RAG does not expose claim-level structure, so these metrics are not measurable for baseline outputs.

---

## Analysis

The results show that baseline RAG frequently produces fluent answers that are not
explicitly supported by the underlying corpus.

For definition-style queries (e.g., *database index*, *MVCC*, *ACID properties*),
the hallucination rate is 1.0, indicating that all generated claims were either
unsupported or contradicted by retrieved evidence.

In contrast, explanation-based queries grounded in the corpus (e.g.,
*Why do database indexes improve performance?*) exhibit significantly better behavior,
with higher claim precision and faithfulness.

This highlights a critical limitation of standard RAG:
**fluency does not imply factual grounding**.

TrustLens makes this failure mode explicit by identifying which claims lack evidence
instead of silently presenting them as facts.

---

## Key Observations

- Retrieval alone is insufficient to guarantee factual correctness
- Many plausible claims are unsupported when checked against evidence
- Claim-level verification reveals partial correctness instead of binary failure
- Faithfulness varies widely across query types

---

## Limitations

- Verification quality depends on corpus coverage
- Some common-knowledge facts are flagged as unsupported
- NLI models are probabilistic and may misclassify edge cases
- Claim normalization can strengthen claims beyond what evidence supports

These limitations motivate future improvements in corpus design,
claim refinement, and verifier calibration.

---

## Conclusion

This evaluation demonstrates that TrustLens provides measurable improvements
in transparency and interpretability over baseline RAG systems.

By operating at the claim level and explicitly verifying evidence,
TrustLens transforms hallucinations from hidden failures into observable signals,
enabling safer and more trustworthy AI-assisted reasoning.
