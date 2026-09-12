# TrustLens ablation plan

## Purpose

An ablation study should identify which parts of the current evidence workflow
change a measured outcome. It must be run against a versioned source set and a
human-reviewed answer key. This repository does not currently publish a valid
ablation result for the current workspace implementation.

## Candidate configurations

| Configuration | Retrieval | Claim and evidence review | Planner specialization | What it tests |
|---|---|---|---|---|
| Full system | Enabled | Enabled | Enabled | Reference implementation. |
| Retrieval only | Enabled | Disabled in review output | Disabled | What a conventional answer experience exposes without evidence contract review. |
| No retrieval | Disabled or fixed empty context | Enabled | Enabled | Dependence on workspace evidence. |
| Whole-answer review | Enabled | Treat answer as one review unit | Enabled | Value of atomic claim granularity. |
| Fixed route | Enabled | Enabled | Disable intent-aware selection | Value of selecting relevant specialists. |

## Experimental controls

- Keep source documents, authority labels, questions, prompt templates,
  provider model/version, thresholds, and application commit fixed per run.
- Preserve the raw answer contracts and reviewer labels.
- Separate provider fallback runs from provider-backed runs.
- Do not assign every claim a positive verdict when a verification component is
  removed; report the missing measurement explicitly.

## Measures

Use evidence precision and recall, human agreement on verdicts, source coverage,
contradiction precision, calibration by confidence band, latency, and failure
rate. Report sample size and uncertainty. The desired conclusion is not that
one mode always gives a higher score; it is which capability makes a specific,
measurable contribution under the documented test conditions.
