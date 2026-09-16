# IWU pilot results

15 September 2026 | Prototype feasibility study | Not independently reviewed

## Verdict

The proposed reference-work arithmetic is implementable and passes the tested accounting properties. The pilot does **not** validate a universal unit of intelligence, reliable real-world performance, or an industry standard. No observed dataset or live run qualifies for audited IWU-E60 certification. The results support a reproducible accounting prototype with explicit measurement gaps.

## 1. Software and structural conformance

60 test methods passed, including 3,000 deterministic randomized cases and 12 checks of the live scoring keys using separately implemented algorithms. A separate Decimal calculation and the standard-library kernel agree with the NumPy retrospective calculation to relative tolerance 1e-12. These are same-author implementation cross-checks. External validation remains open.

Tests cover frozen weights, duplicate credit and charges, retry costs, missing outcomes, incomplete costs, model/effort drift, forbidden-context leakage, future artifacts, broken predecessor links and artifact hash tampering. The structural validator cannot establish that an untrusted capture layer recorded every real action.

## 2. Retrospective external-data feasibility

Outcome-blind selection from a pinned [METR public dataset](https://github.com/METR/eval-analysis-public/tree/52cb829c7a2efb2d659285c4b1768d191d97f8d2) yielded 5,293 recorded episodes, 170 common task IDs and 50 families across four historical aliases. These are newly calculated **reference-minute proxies** under the present accounting rule. Endorsement by METR remains unclaimed. All four aliases come from one vendor, and harnesses vary.

| Recorded system alias | Episodes | Task-macro acceptance | Reference-minute credit / task | Paired-task bootstrap 95% interval |
| --- | ---: | ---: | ---: | --- |
| Claude 3 Opus | 1,381 | 52.6% | 3.02 | 1.97 to 4.19 |
| Claude 3.5 Sonnet (New) | 1,384 | 65.3% | 11.53 | 6.82 to 17.34 |
| Claude 3.5 Sonnet (Old) | 1,381 | 61.3% | 9.10 | 5.63 to 13.26 |
| Claude 4 Opus | 1,147 | 75.7% | 16.58 | 11.18 to 22.70 |

The intervals use 10,000 paired task resamples, PCG64 seed 20260915 and linear percentile quantiles. They describe workload-resampling uncertainty conditional on recorded outcomes and weights. They omit human-calibration uncertainty, unseen attempts, contamination and judge uncertainty. Family-cluster intervals and all six paired differences are included in METRICS.json.

### Reliability findings worth disclosing

- Reference weights are concentrated: the longest 17 tasks (10%) carry 63.7% of the total weight. The weight-based effective task count is 31.9, compared with 170 raw task IDs. This concentration statistic is not a substitute for inferential sample size.
- Across 1,000 within-task split-half partitions, the full four-system ranking disagreed in 11.5% of partitions. Median rank correlation was 1.00, and measurement reliability requires additional evidence on absolute score stability.
- Median absolute split-half disagreement relative to each full-sample score ranged from 10.3% to 17.9%.
- Rankings did not change under equal-family weighting, removal of the longest 10% of tasks, or 1,000 independent +/-20% weight perturbations. Absolute levels did change materially; the changed-workload scores are not interchangeable units or measured calibration-error intervals.
- 19 of 170 human-time weights are explicitly labeled estimates. 104 task IDs have multiple version labels; 69 have a missing version somewhere. **Zero tasks meet the strict single, non-missing version requirement across all four aliases.** These counts overlap. No conformant frozen-version subset can be reported.
- No selected-alias row failed the numerical eligibility filter and no task was removed for inconsistent human minutes. Original artifact, verifier, complete-context and cost provenance remain unverified. Fatal-error outcomes were retained.

| Alias | Equal-family score | Original uniform-task score | Drop longest 10% score |
| --- | ---: | ---: | ---: |
| Claude 3 Opus | 3.63 | 3.02 | 3.35 |
| Claude 3.5 Sonnet (New) | 23.09 | 11.53 | 10.46 |
| Claude 3.5 Sonnet (Old) | 17.90 | 9.10 | 7.50 |
| Claude 4 Opus | 29.72 | 16.58 | 14.52 |

Values are reference-minute credit per assigned task under each distinct workload. For example, the newer Sonnet versus older Sonnet paired interval includes zero; the Opus 4 versus newer Sonnet family-cluster interval also includes zero. These descriptive comparisons are not controlled model effects or current purchasing recommendations.

## 3. Prospective live instrumentation

Six fresh ephemeral sessions requested the same model (gpt-5.6-sol) and reasoning effort (medium): three direct-answer sessions and three local-computation-allowed sessions, alternating direct then assisted within each replicate. The fixed battery contains four arithmetic, four directed shortest-path and four constrained-subset items.

| Condition | Sessions | Accepted answers | Mean elapsed / session | Input tokens | Output tokens | Observed command events |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| direct | 3 | 36/36 | 65.0s | 32,519 | 8,109 | 0 |
| local_computation | 3 | 36/36 | 38.9s | 106,084 | 5,483 | 3 |

All 72 scored responses were correct on these 12 reused items. No observed schema or disallowed-tool-type violation was recorded. This is not a 72-independent-task study, and no general reliability confidence interval is inferred from it. The perfect scores suggest a ceiling effect; this battery does not distinguish work capacity or prove tool use improves accuracy.

Available CLI usage includes cached-input and reasoning-output fields, retained separately in METRICS.json. They are not added again to input/output totals. The capability probe is excluded from scores and condition totals; its usage is disclosed separately. There were no silent reruns or model substitutions. Each scored session had a 180-second wall cap. Temporary worker directories were removed; only final JSON, scores, usage and sanitized event metadata/command hashes remain.

**Certification gaps:** effective model/effort identity was not exposed by these CLI events; only requested settings are known. Command bodies were not retained, so their hashes provide commitments with replayability unavailable. The trace adapter therefore does not satisfy full audit requirements. No human-time weights were assigned to these toy items and no per-episode bill was available. Accordingly, live IWU, dollar efficiency and cost-savings claims are withheld.

## 4. What this supports

The prototype includes the formula, registry/episode contract, original calculator, structural checks, transparent proxy reanalysis, small deterministic smoke test and a plan to falsify the metric. No certification gate was relaxed to obtain a headline.

Still needed: independently timed human baselines; prospective frozen tasks; cross-provider and cross-harness replication; trusted traces and invoices; independent implementations; judge agreement on open-ended tasks; held-out tests of predictive usefulness; and open standards governance. See VALIDATION-ROADMAP.md.

## Reproducibility and disclosure

Dataset commit: `52cb829c7a2efb2d659285c4b1768d191d97f8d2`. Raw SHA-256: `f489d11728909937dad99ba1ed2d7c40efe12a766891e67dbc7c2486a3311236`. Protocol SHA-256: `b047bc26f388355787e13dca6fb81d5f4bbb29c06e96dbff4db338d96e2bc05a`. The protocol was saved locally before outcome analysis; it was not externally timestamped or formally preregistered. Schema/version quality notes were saved before statistics. Reporting and formatting work followed analysis.

The raw upstream dataset and upstream code are excluded. Source provenance and a pinned retrieval script support independent reanalysis. The live trials requested gpt-5.6-sol at medium effort. Independent human statistical review and human-time calibration remain open.

## 5. Supplemental pre-release falsification pass

The supplemental plan was recorded after the primary pilot and before its own outputs. Its analyses retain the original primary selection.

All 12 of 12 deliberately introduced faults were caught by the tests. Fault coverage is limited to the hand-selected mutation suite. Numeric overflow and malformed trace-field checks were hardened, and 1,000 additional randomized monotonicity/bounds cases were added.

### Test the meaning of a confidence interval

Three fully synthetic scenarios, 1,000 experiments each, test interval behavior against known fixed-registry truth. Each experiment used 500 task-bootstrap resamples. Simulations are not additional model runs and are not human calibration.

| Synthetic scenario | Task-bootstrap coverage of fixed-registry truth | Monte Carlo SE | Bounded-sum coverage |
| --- | ---: | ---: | ---: |
| ordinary_independent | 98.6% | 0.37 percentage points | 99.9% |
| concentrated_reference_weights | 99.2% | 0.28 percentage points | 99.6% |
| near_ceiling | 38.9% | 1.54 percentage points | 100.0% |

**Do not turn conditional task-resampling intervals into blanket 95% accuracy guarantees.** Near the ceiling, the percentile interval can collapse on all-success observations. This deliberate test addresses an overbroad fixed-registry interpretation. The original intervals retain their workload-conditional uncertainty target. The added Hoeffding-based bounded-sum interval is conservative and valid only under independent bounded blocks, fixed weights and complete correct outcomes. It does not solve human-calibration uncertainty, hidden dependence or unrepresentative tasks.

### Cross-provider feasibility, exploratory

Availability-based selection of one alias in each of four named provider strata yields 5,477 records on 170 task IDs. These overlap the primary analysis and must not be added as independent samples. Each provider's fullest-coverage alias was selected before its supplemental score was calculated, with alphabetical ties.

| Provider | Historical alias | Records | Reference-minute proxy / task | Conditional task interval |
| --- | --- | ---: | ---: | --- |
| Anthropic | Claude 3 Opus | 1,381 | 3.02 | 1.97 to 4.21 |
| OpenAI | GPT-4 0125 | 1,382 | 2.14 | 1.27 to 3.24 |
| Google | Gemini 2.5 Pro Preview | 1,359 | 10.10 | 6.74 to 14.08 |
| DeepSeek | DeepSeek-R1-0528 | 1,355 | 11.52 | 8.29 to 15.05 |

This supports data-processing portability across recorded providers. Measurement invariance and controlled comparisons require additional studies. Again, zero tasks meet the single non-missing version gate across selected systems; all scores remain proxies.

### Counterexamples and launch decision

Deterministic counterexamples show that changing workload weights can reverse rankings, equal IWU can hide different per-task reliability, dropping missing outputs inflates acceptance, averaging efficiency ratios gives the wrong accounting result, and common-mode human-time errors can move all scores without changing rankings. See RED-TEAM-REPORT.md and CLAIM-AUDIT.md.

**Decision: suitable as a tested draft/RFC inviting falsification. Not suitable for a calibrated, universally accurate, independently validated or adopted-standard claim.**

## 6. Correcting the uncertainty rule

The point estimator is unchanged. The specification now includes block-aware bounded-sum intervals and a one-sided lower-confidence quantity, IWU-L95. This reports a conservative floor on expected fixed-registry credit under explicit assumptions. Next-task reliability has a separate validation target.

A fresh 12,000-experiment synthetic suite covered ordinary, concentrated, near-ceiling, near-floor and correlated outcomes. Correctly block-aware two-sided coverage ranged from 99.2% to 100.0%; lower-bound validity ranged from 99.5% to 100.0%. The results show conservative coverage relative to nominal 95% for the declared synthetic designs. Real-system coverage requires justified assumptions and validation.

Ignoring dependence still fails. Correct grouping can produce wide or even vacuous intervals; the reporting contract retains them with their assumptions. The theorem requires truthful fixed bounds and independent blocks, a fixed sample plan and appropriate handling of calibration/missingness. No empirical IWU certification is added by this correction. Full formulas, widths, Monte Carlo intervals and examples are in UNCERTAINTY-CORRECTION.md and METRICS.json.
