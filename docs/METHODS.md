# Study methods

Study identifier: `iwu-validation-v01`. Study date: 15 September 2026. Reference profile: IWU-E60. This document is a public, post-analysis methods account.

## Evidence provenance

The original protocol was recorded locally before outcome analysis. External preregistration and independent timestamping were unavailable. Its SHA-256 is `b047bc26f388355787e13dca6fb81d5f4bbb29c06e96dbff4db338d96e2bc05a`. That historical commitment is retained in `SELECTION-LOCK.json` and the recorded results. The original operational protocol remains in the study archive; this public methods account has its own release-manifest digest.

Public export preserves numerical results, source commitments, sanitized final answers and core accounting functions. The portable analysis entry point verifies the pinned dataset, historical protocol commitment and locked selection. It reads this repository's numerical inputs independently of the archived operational environment.

## Accounting and structural conformance

The standard-library calculator computes task-macro work credit, identified unknown-outcome bounds and complete episode-cost accounting. Fixtures test duplicate credit, overlap in charge coverage, missing outcomes, invalid numbers, conservation of partial deliverables, model/effort drift, forbidden context and artifact links. Sixty test methods include 3,000 deterministic randomized cases. A selected mutation suite probes 12 named faults.

The structural audit establishes consistency among supplied records. Authenticity and completeness require trusted source capture and independent evidence.

## Retrospective selection and estimation

Source: `METR/eval-analysis-public`, commit `52cb829c7a2efb2d659285c4b1768d191d97f8d2`, file `reports/time-horizon-1-0/data/raw/runs.jsonl`. Verify SHA-256 `f489d11728909937dad99ba1ed2d7c40efe12a766891e67dbc7c2486a3311236` before analysis.

Eligible rows have a nonempty alias and task identifier, finite positive `human_minutes`, and binary `score_binarized`. Human aliases are excluded. Rank system aliases by the number of tasks with at least four eligible repetitions, with alphabetical ties. Select the top four and their shared tasks with at least four repetitions in every selected alias. Exclude tasks with inconsistent reference minutes or task-family labels. The prespecified minimum is 30 usable common tasks; substitution is forbidden.

Uniform probabilities across common tasks define the primary workload. Average acceptance within each task and multiply by its frozen imported reference minutes. Imported weights remain provisional. The primary sample contains 5,293 episodes, 170 task IDs and 50 families. Full selection and version-quality results are in `results/PUBLIC-METRICS.json`.

Use NumPy PCG64, seed `20260915`, for 10,000 paired task-bootstrap resamples; percentile intervals use linear quantiles. Family-cluster resampling uses seed `20260916`. Split-half repeatability uses 1,000 within-task partitions and seed `20260917`. Additional weight-perturbation seeds and operations are explicit in `scripts/analyze_public.py`.

The bootstrap estimates task-resampling sensitivity conditional on recorded outcomes and weights. Fixed-registry execution uncertainty and calibration uncertainty are separate targets. Sensitivity analyses cover equal-family weighting, removal of the longest 10% of tasks and 1,000 independent +/-20% reference-weight perturbations.

## Live instrumentation smoke test

Six fresh sessions requested `gpt-5.6-sol` with medium reasoning effort. Three used direct answers and three allowed local computation, alternating by replicate. Twelve deterministic tasks comprise four arithmetic, four directed shortest-path and four constrained-subset items, generated with seed `20260915`. Each session had a 180-second cap and one execution attempt. A capability probe is excluded from scored outcomes.

Recorded evidence contains final-answer JSON, acceptance, available usage and sanitized event metadata. All 72 scored answers were accepted. The same 12 items were reused across sessions, and the battery has a ceiling effect. Effective-model attestation, human calibration, full replayable tool bodies and invoice-backed costs were unavailable. Certified work credit and full-cost efficiency are therefore unavailable for the live sample.

## Synthetic uncertainty experiments

The first stress suite uses three scenarios, 1,000 experiments per scenario, 500 task-bootstrap resamples per experiment, and seeds `20260930` through `20260932`. It probes an overbroad fixed-registry interpretation of task-bootstrap intervals. Near-ceiling coverage is 38.9%.

The correction suite uses six scenarios, 2,000 experiments per scenario, 500 bootstrap resamples per experiment, and seeds `20261101` through `20261106`. Scenarios cover ordinary, concentrated, near-ceiling, near-floor, family-correlated and fully correlated outcomes. They compare task-bootstrap, trial-independent and correctly block-aware procedures.

IWU-L95 applies a one-sided bounded-sum inequality with `ln(20)`; the two-sided 95% interval uses `ln(40)`. Both require correct fixed bounds, independent blocks and a fixed sample plan. Missing assigned outcomes remain represented in block ranges. The correction suite records coverage, Monte Carlo uncertainty, width and lower-bound validity in `results/UNCERTAINTY-CORRECTION.json`.

## Interpretation

This is a prototype feasibility study. Human calibration, open-ended judge validation, independent capture, cross-harness replication and predictive utility require additional experiments. Workload identity, weights, acceptance gates and evidence completeness are part of every interpretable score.
