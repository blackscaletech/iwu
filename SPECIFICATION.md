# IWU: Inference Work Units

Request for comment, draft 0.1 - 15 September 2026

**Proposed reference-work accounting convention. Scores are conditional on a named workload and expert-time profile. Adoption and independent calibration remain open.**

## 1. The definition

IWU stands for **Inference Work Units**. The first technical reference profile is **IWU-E60**: E60 identifies 60 active reference-expert seconds per unit. Public discussion may use IWU; score records retain the full profile identifier so future calibration profiles remain distinguishable.

One **IWU-E60** is one minute of frozen reference-expert task effort credited to an independently accepted deliverable, under a named, versioned task registry. E60 denotes 60 active expert seconds. “Inference” describes the AI service being accounted for. The unit is a task-dependent accounting convention.

The reference expert cohort, permitted human tools, quality threshold, task inputs and calibration procedure are part of the definition. A minute in one domain is not claimed to have the same economic value or cognitive difficulty as a minute in another. Comparisons require the same workload, registry, quality criteria, operating boundary and budget policy.

The calculation applies across model architectures within a named reference profile. Comparability requires matched workload definitions and evidence boundaries.

## 2. Normative equations

Let registry R contain tasks i = 1,...,N. Freeze:

- pi_i > 0, sum pi_i = 1: the target workload distribution;
- t_i: calibrated active reference-expert seconds, with cohort and uncertainty provenance;
- h_i = t_i / 60: the task's IWU-E60 weight;
- V_i: a versioned acceptance function applied to final output and permitted observable evidence;
- S: model, version, reasoning setting, harness, tools, memory policy and permissions;
- b: time, cost, retry and assistance limits applying to an externally assigned episode.

For the j-th independent episode on task i, Y_ij = V_i(output_ij, evidence_ij) is either 0 or 1. Failed attempts, timeouts and refused tasks receive 0 **when that disposition is observed and the frozen acceptance policy specifies rejection**. Missing or unauditable outcomes remain unknown and stay in the assignment denominator.

\[
\widehat W_{R,\pi}(S,b)
= \sum_{i=1}^{N}\pi_i h_i\left(\frac{1}{n_i}\sum_{j=1}^{n_i}Y_{ij}\right)
\quad\text{IWU-E60 per assigned task.}
\]

Here n_i is the number of **scheduled episodes**, including every disposition. Internal retries belong to the same episode. Averaging within tasks before weighting avoids overweighting tasks with more sampled repetitions. For an actual production ledger, delivered reference-work credit is sum_episode h_task Y_episode; benchmark repetitions estimate an expectation and must not be marketed as distinct economically useful deliveries.

Let C_ij be total episode cost at the declared boundary, including failed attempts, tool/provider charges, allocated infrastructure, and paid human intervention where in scope. Let L_ij be end-to-end elapsed time; child-span times are not added as wall time.

\[
\widehat C=\sum_i\pi_i\frac{1}{n_i}\sum_j C_{ij},
\qquad
\widehat\eta_C=\frac{\widehat W}{\widehat C}.
\]

Use the **ratio of weighted means**. Averaging per-run ratios is an invalid estimator for this definition. Report the currency, price date, actual versus estimated charges, cost boundary and completeness. If costs are incomplete, a full-cost IWU/currency estimate is unavailable. A zero observed denominator is not infinite certified efficiency. Energy, latency and tokenizer-specific token counts may be separate resource axes; they cannot be added into a unitless efficiency score without explicit valuation weights.

For unknown outcomes U_i and observed accepted count A_i, report identified bounds:

\[
W^- = \sum_i\pi_i h_i A_i/n_i,
\qquad
W^+ = \sum_i\pi_i h_i(A_i+U_i)/n_i.
\]

These are identified missingness bounds. Sampling uncertainty and calibration uncertainty must be reported separately or jointly modeled under a declared procedure.

## 3. No free credit for decomposition

Default: one external task, one acceptance decision, one fixed weight. Ten internal subtasks do not become ten external deliverables. A tool call or extra token earns no credit by itself.

If partial deliverables are genuinely useful, a registry may define independent acceptance atoms **before execution**, with fractions alpha_ik > 0 summing to 1. Episode credit is h_i sum_k alpha_ik Y_ijk and is bounded by h_i. Parent plus child credit must not both be counted. Splitting one accepted atom conserves its original fraction. Declaring independently useful atoms requires human governance and supporting evidence.

## 4. Expert calibration

The initial candidate calibration profile is the median active time of independently accepted human completions, with a prespecified expertise screen, tool policy and interruption handling. Human setup, reading, editing, testing and correction count; unrelated breaks do not. Record all human non-completion and censoring under the prespecified policy. If the chosen estimand is not identifiable with adequate precision, the task remains uncalibrated. Median accepted-completion time is conditional on completion, and is not unconditional expected human time to success.

Freeze accepted weights for a registry version. Model improvement must not reduce a task's weight. New tasks need calibration; revised human workflows create a new profile. Publish uncertainty and require independent replication before a “calibrated” certification label. Expert estimates, model-generated times and imported legacy numbers are explicitly **proxy weights** until verified against that profile.

Calibration requires human data, uncertainty analysis, reference governance and a validated cross-registry bridge. These remain research priorities.

## 5. What trace evidence is required

A conformant result requires:

1. Frozen task, rubric, input and system-configuration commitments; a pre-execution assignment manifest.
2. Requested and effective model/version and reasoning setting, including fallback or routing events. Unknown effective identity is a disclosed certification failure.
3. Episode/span IDs, parent and artifact-predecessor links, monotonic timestamps, status and retry lineage. Declared inputs must match consumed inputs; future artifacts and evaluator feedback cannot leak into solving.
4. Observable tool identity, permitted arguments/results or auditor-accessible commitments, and side-effect boundaries. Sensitive content can stay private; hashes alone do not prove what happened or that nothing is missing.
5. Final artifacts and versioned verifier records, with acceptance independently reproducible. LLM judges require blinded candidates, fixed judge settings, human agreement studies and judge-sensitivity reporting.
6. Disjoint primitive charge IDs linked to provider invoices or equivalent evidence. Inclusive parent charges cannot also include already counted child charges. Cached tokens and reasoning tokens must follow provider definitions; subsets must not be added twice.
7. Complete scheduled-episode disposition, including failed, missing, invalid and superseded attempts. Benchmark execution and evaluation costs are disclosed separately, with the scored operating boundary explicit.

No chain-of-thought or private internal model reasoning is required or collected. Outcome verification and externally observable execution evidence are sufficient for the proposed accounting boundary. A trusted capture layer is still needed to establish trace completeness.

The prototype scope comprises an accounting kernel and a structural trace validator. Its checks reject inconsistent declared records. Trusted capture, billing reconciliation, portable adapters and certification governance require additional systems and independent processes. Detecting coordinated source-record falsification requires externally anchored evidence.

OpenTelemetry's [GenAI attributes](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/) offer existing names for model and usage telemetry. An IWU adapter should extend that work with workload, acceptance, calibration and episode-accounting commitments.

## 6. Reliability and interpretation

Report task-macro acceptance, work-weighted acceptance, W, full-cost efficiency when available, task/family distributions, baseline-weight concentration, repeatability, missingness, and uncertainty. A single leaderboard number is insufficient.

Use paired workload resampling for system comparisons and account for task-family dependence. Reference-time uncertainty, judge uncertainty, repeated-attempt noise and task-distribution uncertainty are different sources of error. Stable rankings do not establish stable absolute work or price levels.

### Explicit properties and uncertainty boundaries

With frozen nonnegative weights, `dW/dp_i = pi_i h_i >= 0`: better acceptance on any task cannot reduce W while all other probabilities stay fixed. Also `0 <= W <= sum_i pi_i h_i`. These are established consequences of the linear definition. Fixed atomic fractions conserve a parent task's maximum credit. None of these properties implies that h_i accurately represents human effort or that W predicts buyer utility.

The default workload bootstrap estimates sensitivity to task resampling conditional on recorded outcomes. It MUST NOT be labeled a guaranteed interval for true future task acceptance, particularly on small all-success/all-failure samples. The supplemental simulation demonstrates why.

For a *fixed* registry and independent bounded episode contributions X_l in [0,a_l], a conservative interval for the expected sum can use a Hoeffding radius:

\[
\epsilon_\alpha=\sqrt{\tfrac12\log(2/\alpha)\sum_l a_l^2},
\qquad
I=[\widehat W-\epsilon_\alpha,\widehat W+\epsilon_\alpha]
\cap[0,\sum_i\pi_i h_i].
\]

For independent task trials, `a_ij = pi_i h_i / n_i`. Dependent observations must be grouped into independent blocks with correspondingly larger range bounds, or another justified procedure used. The bound follows from [Hoeffding's classical inequality](https://www.tandfonline.com/doi/abs/10.1080/01621459.1963.10500830). The implementation is in `uncertainty.py`. It is often wide; independence, fixed truthful weights and correct complete outcome capture are assumptions requiring independent justification. Human calibration and future-workload uncertainty require separate treatment.

### Corrected reliability-sensitive reporting: IWU-L95

Keep the point estimand W unchanged. Report a separate one-sided lower-confidence credit with its own uncertainty interpretation. Let G partition all scheduled contributions into independent blocks, and let `B_g = sum_(i,j in g) pi_i h_i / n_i`. Define:

\[
\boxed{\operatorname{IWU\!\!\!-L}_{1-\alpha}
=\max\!\left\{0,\widehat W^{-}
-\sqrt{\frac{\log(1/\alpha)}{2}\sum_{g\in G}B_g^2}\right\}.}
\]

W_hat^- counts observed accepted credit; every unobserved assigned outcome stays uncredited **for this lower bound only**. The point estimate remains unavailable when missingness prevents its identification. Since the lower observed credit cannot exceed the complete latent observed credit, the lower-confidence result does not require missing-at-random assumptions. All scheduled contributions must still be included in the block ranges.

At alpha = 0.05, IWU-L95 is a conservative 95% lower confidence bound on **expected reference-work credit for the fixed registry and policy**. It is not a 95% chance of next-task success. Under correctly specified independent bounded blocks, its coverage follows from Hoeffding's one-sided inequality. If dependence is unknown, group conservatively; one fully dependent experiment may yield only a zero lower bound. Do not assume independence to obtain a narrower interval.

The sample plan must be fixed in advance. Repeated peeking, adaptive stopping and post-selection require a separately valid sequential or multiplicity correction. Significance testing requires paired expected-credit differences under a declared joint uncertainty procedure. More samples can improve a lower bound without improving the system, so report sample counts and block structure with every lower-bound comparison.

For uncertain human weights, certification additionally needs simultaneous calibration intervals. One conservative construction uses all h_i lower calibration bounds and splits the allowed error between calibration and episode sampling (alpha_calibration + alpha_sampling <= alpha_total), with a justified conditional design. This proposed extension requires empirical calibration and independent validation. Without calibration evidence, both W and IWU-L95 remain conditional reference-weight quantities.

See UNCERTAINTY-CORRECTION.md for the fresh synthetic tests, including near-ceiling, near-floor and dependence failures. The proposed correction improves the uncertainty contract. Accuracy of human weights and construct validity require independent empirical evidence.

An increasing difficulty ladder provides a complementary capability scale. For example, an anchored item-response model may estimate P(success) = logistic(theta - d_i). That capability scale carries explicit model assumptions and requires additional calibration to establish an additive work interpretation. Adjacent-item overlap helps link the scale. Unidimensionality and conversion to expert minutes require additional evidence. [Stanford's IRT evaluation work](https://crfm.stanford.edu/2025/06/04/reliable-and-efficient-evaluation.html) is relevant prior art.

Work credit is not measured time saved, cognitive difficulty, usefulness to every buyer, guaranteed reliability, or economic value. Harmful outputs and policy violations fail the applicable acceptance gate; acceptance criteria themselves remain accountable to the workload owner.

## 7. Conformance labels and change control

| Label | Meaning |
| --- | --- |
| Accounting prototype | Arithmetic and declared-record checks passed on fixtures. |
| Reference-work proxy | Outcome-weight calculation with provisional human times and/or incomplete provenance. |
| Audited IWU-E60 profile | Independently calibrated registry, complete audited episode evidence, known system identity, and published uncertainty. **No result in this pilot earns this label.** |
| Industry standard | Open governance, cross-implementation interoperability, independent deployment and community adoption. **Not established here.** |

Every score identifier must include specification version, registry hash, workload profile, system configuration and budget boundary. Do not join revised registries by name alone. Specify cross-language canonical bytes before interoperability certification; the Python helper's sorted-JSON encoding is not claimed to implement RFC 8785.

Open issues before 1.0: human calibration profile; censored human attempts; domain-specific acceptance; independent traces and bills; portable serialization; cross-provider accounting; privacy-preserving audit; cross-registry comparability; governance and licensing. See `VALIDATION-ROADMAP.md`.
