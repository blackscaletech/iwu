# Correcting IWU's uncertainty rule

The expected-work formula is unchanged. The error was the temptation to treat one uncertainty procedure as a universal guarantee.

## The corrected reporting object

Report `(W_hat, interval, IWU-L95, registry, calibration status, block assumptions, sample plan, completeness)` together. W_hat is the original weighted-work estimate. IWU-L95 is a conservative lower confidence bound on expected fixed-registry work credit. The exact formula and assumptions are in SPECIFICATION.md.

Let B_g be the maximum possible contribution of independent block g. The one-sided uncertainty margin is `sqrt(log(1/alpha) * sum_g B_g^2 / 2)`. Subtract it from observed accepted credit and clip at zero. For a two-sided interval, use `log(2/alpha)`. This applies a classical probability bound.

## Fresh synthetic validation

12,000 synthetic experiments: 2,000 per scenario, 500 task-bootstrap resamples each. Integer seeds, coverage Monte Carlo intervals and interval widths are recorded in results/UNCERTAINTY-CORRECTION.json. These are not LLM executions or calibrated human observations.

| Scenario | Misapplied task-bootstrap coverage | Trial-independent bound coverage | Correct block-aware coverage | Correct lower-bound validity |
| --- | ---: | ---: | ---: | ---: |
| ordinary_independent | 98.25% | 99.65% | 99.65% | 99.50% |
| concentrated_weights | 98.20% | 99.20% | 99.20% | 99.65% |
| near_ceiling | 38.80% | 100.00% | 100.00% | 100.00% |
| near_floor | 38.45% | 100.00% | 100.00% | 100.00% |
| family_correlated | 86.95% | 37.65% | 100.00% | 100.00% |
| whole_sample_correlated_negative_control | 0.00% | 0.00% | 100.00% | 100.00% |

Coverage is the fraction of intervals containing the known expected credit. Lower-bound validity is the fraction of lower bounds not exceeding that truth. The first column deliberately tests an overbroad fixed-registry interpretation. The original workload-conditional estimand remains separate.

**The correction works for the stated synthetic designs, conservatively.** It does not rescue a false independence assumption. In the fully dependent negative control, the correct interval is [0,1] and the lower bound is zero. These bounds express the limited available information.

| Scenario | Mean correct interval width | Mean correct lower-confidence credit | True expected credit |
| --- | ---: | ---: | ---: |
| ordinary_independent | 0.1753 | 0.4208 | 0.5000 |
| concentrated_weights | 3.8682 | 1.1825 | 2.9750 |
| near_ceiling | 0.2063 | 0.8131 | 0.9900 |
| near_floor | 0.2062 | 0.0000 | 0.0100 |
| family_correlated | 0.9235 | 0.0581 | 0.5000 |
| whole_sample_correlated_negative_control | 1.0000 | 0.0000 | 0.5000 |

## A simple illustration

For 48 genuinely independent, equally weighted binary observations with all successes and maximum credit normalized to one, the point estimate is 1.000 and IWU-L95 is 0.8233. The uncertainty margin is 0.1767. This is a standalone numerical illustration. Live human calibration remains unavailable.

## Scope of the correction

- Corrected: uncertainty does not collapse to false certainty merely because the observed sample is all successes or all failures.
- Corrected: known within-block dependence can be accommodated by larger block ranges; missing assigned outcomes can conservatively widen bounds without assuming random missingness.
- Not corrected by mathematics alone: inaccurate human-time weights, unobserved cost, hidden dependence, unaudited traces, task leakage, changing systems, or an unrepresentative registry.
- Interpretation: sample size and sampling design affect a lower bound independently of changes to the system. Report the point estimate and bound together.
- Not established: calibrated 95% real-world labor savings or next-task success guarantees. Independent human calibration and a validated operating environment remain prerequisites.
