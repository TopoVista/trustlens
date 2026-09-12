# TrustLens evaluation plan

## Status of previous results

Earlier repository notes contained small baseline outputs from an older database-systems corpus and an earlier verification implementation. They are not current production benchmarks and must not be used to claim the quality of the current workspace product.

## What to evaluate now

Evaluate the product on a versioned, consented source set that resembles the intended use case. Record the workspace sources, queries, expected evidence, provider configuration, thresholds, and application commit for each run.

| Measure | Question it answers |
|---|---|
| Evidence precision | Are linked passages genuinely relevant to the displayed claim? |
| Evidence recall | Does the answer surface the important source passages available in the workspace? |
| Claim verdict agreement | Do human reviewers agree with supported, contradicted, and unresolved labels? |
| Citation or source coverage | What share of factual answer claims have a linked workspace source? |
| Contradiction precision | Are surfaced conflicts actually incompatible in their source context? |
| Calibration | Do higher confidence bands correspond to higher human-rated support? |
| Latency | How long do ingestion, retrieval, and full query paths take under intended deployment conditions? |

## Recommended protocol

1. Build a fixed source corpus with a documented authority assignment.
2. Write question sets for direct facts, comparisons, timelines, conflicts, deliberately unsupported questions, and paraphrases.
3. Have at least two human reviewers label expected support and evidence spans.
4. Run the exact same questions with versioned settings and preserve raw answer contracts for review.
5. Compare automatic outputs to human labels and report confidence intervals or sample sizes rather than only percentages.
6. Repeat after changes to retrieval, prompting, provider models, thresholds, ingestion, or source normalization.

## Reporting language

Report `UNRESOLVED` or `NOT_SUPPORTED` as a limitation of available workspace evidence, not a claim that the proposition is false. Report provider fallback runs separately from provider-backed runs. Do not average together results from different corpora, model versions, or sources without saying so.
