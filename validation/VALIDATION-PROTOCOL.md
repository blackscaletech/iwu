# IWU-S20 centered-surprisal candidate validation protocol

Date locked: 2026-09-18
Status: pre-implementation falsification protocol

## Why this replaces the first bit candidate

The relative-log-score candidate can reward a system for accurately forecasting
its own low acceptance rate. For endogenous outcomes such as agent success, that
is predictive information but not useful work. IWU-S20 must have positive expected
value if and only if verified acceptance improves over the frozen reference.

## Candidate definition

For episode `i`:

- `A_i` is an automatically verified acceptance indicator in `{0,1}`;
- `p_i` is the frozen reference policy's probability of acceptance for that task
  or predeclared stratum;
- `d_i = -log2(p_i)` is the reference surprisal of success.

The episode score is:

`IWU_i = ((A_i - p_i) / (1 - p_i)) * d_i`.

Equivalent realized values are:

- accepted: `IWU_i = -log2(p_i)`;
- rejected: `IWU_i = [p_i log2(p_i)] / (1-p_i)`.

Thus a reference-policy success has zero expected score, rare verified successes
earn more bits, and failures receive the unique debit that centers the reference
expectation at zero while retaining the success surprisal scale.

The S20 profile represents `p_i` as integer ticks out of `2^20`. Empirical binary
references use the Krichevsky–Trofimov estimate
`p_i = (successes + 1/2) / (trials + 1)` before deterministic tick quantization.
Analytically known reference probabilities may be supplied directly.

## Unit definition

> 1 IWU is one bit of reference-centered, verified success surprisal.

The aggregate is additive work delivered over a declared workload. The normalized
quantity is IWU per attempted episode. Resources remain separate, enabling
IWU/USD, IWU/J, IWU/s, and IWU/token.

## Mandatory gates

### S1 — reference zero

For all valid `p`, `E[IWU | A ~ Bernoulli(p)] = 0` analytically and to numerical
tolerance. Maximum absolute error over at least 100,000 randomized references must
be below `1e-12`.

### S2 — directional usefulness

For treatment acceptance probability `q`, expected IWU must be positive exactly
when `q > p`, zero when `q = p`, and negative exactly when `q < p`.

### S3 — bit realization

An accepted episode must earn exactly `-log2(p)` at the represented S20
probability. At `p=1/2`, acceptance must equal `+1 IWU` and rejection `-1 IWU`.

### S4 — additivity and mergeability

Whole-ledger and independently sharded sums must agree within `1e-12`. Uniform
duplication doubles total IWU and leaves IWU/event unchanged.

### S5 — architecture neutrality

The identical record function must score language, random-forest, structured Jev,
and agent pass/fail records. No model or tokenizer field may enter the formula.

### S6 — no human comparison in the core

Core conformance accepts only a frozen automatic binary verifier. Human labels may
be used to create a benchmark but may not be required at runtime.

### S7 — reference traceability and anti-gaming

Every record must carry registry, verifier, and reference identities. Mixed
identities, duplicate episode IDs, post-outcome reference mutation, and undeclared
missing records must fail closed. The report must show reference trial counts or
the analytical-reference method.

### S8 — finite-boundary behavior

S20 must yield finite scores at all representable probabilities. Direct-floor,
Jeffreys/KT, and Laplace sensitivity must be disclosed for empirical zeros/ones.
No silent clipping is allowed.

### S9 — non-redundancy and value

On the existing 57-group holdout, report exact relationships to raw delta utility,
rank/sign changes, resource relationships, and whether difficulty weighting changes
any decisions. A change is not automatically an improvement; it must be explicable
by the frozen reference difficulty.

### S10 — dependence-aware uncertainty

Intervals must resample declared independent blocks. A 10,000-run clustered-null
simulation must show observation-level intervals materially under-covering and
block-level intervals within 1.5 percentage points of the nominal 95% coverage.

### S11 — cross-language conformance

Python and JavaScript implementations must match on fixed boundaries and at least
100,000 deterministic randomized records, including reference ticks and record
hashes. No mismatch is allowed.

### S12 — resource separation and integration simplicity

Changing tokens, dollars, joules, latency, or model identity must not change IWU.
The public integration must require one post-verification record call and no
model-specific adapter beyond producing the automatic acceptance boolean.

## Kill conditions

Reject or revise the candidate if:

1. expected sign does not exactly track acceptance uplift;
2. empirical zeros/ones dominate results under reasonable KT estimation;
3. rankings are primarily probability-floor artifacts;
4. identical records disagree across languages;
5. reference selection cannot be made auditable;
6. the implementation requires model probabilities or human pairwise judgments;
7. the result has no interpretable difference from raw accuracy after conditioning
   on reference difficulty.

## Claim boundary

Surprisal, Bernoulli residuals, KT estimation, and control comparisons are prior
art. The candidate's possible contribution is their exact synthesis into a small,
cross-model inference-work unit and conformance protocol. It must not be called an
industry standard or independently validated before outside replication.
