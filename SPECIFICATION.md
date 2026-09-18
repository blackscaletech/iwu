# IWU-S20 specification

Version: `IWU-S20/0.2-draft`
Status: open standard candidate

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are
normative requirements.

## 1. Scope

IWU-S20 defines an additive score for automatically verified binary outcomes
relative to a frozen reference policy. It is architecture-neutral: the measured
system may be an LLM, classifier, agent, structured inference engine, vision
model, ensemble, or conventional algorithm.

IWU-S20 does not replace resource telemetry. Tokens, currency, time, energy,
memory, and tool calls remain separate quantities.

## 2. Definition

For episode `i`:

- `A_i` is the verifier result in `{0,1}`;
- `p_i` is the represented reference probability in `(0,1)` for the declared
  task stratum;
- `d_i = -log2(p_i)` is reference success surprisal in bits.

The episode score is:

```text
IWU_i = ((A_i - p_i) / (1 - p_i)) × d_i
```

Equivalent realized values are:

```text
accepted:  IWU_i = -log2(p_i)
rejected:  IWU_i = p_i log2(p_i) / (1 - p_i)
```

The aggregate is `sum(IWU_i)`. The normalized descriptive quantity is
`sum(IWU_i) / attempted episodes`.

### 2.1 Unit

One IWU is one bit of reference-centered verified success surprisal.

This is an information-denominated accounting convention. It is not a claim that
one IWU corresponds to a fixed amount of hardware computation, human labor,
energy, money, or intelligence.

### 2.2 Centering and direction

For a candidate with pass probability `q_i`:

```text
E[IWU_i] = ((q_i - p_i) / (1 - p_i)) × -log2(p_i)
```

Therefore expected IWU is positive exactly when `q_i > p_i`, zero when
`q_i = p_i`, and negative when `q_i < p_i`.

The rejection debit is uniquely fixed once two axioms are selected:

1. acceptance earns `-log2(p)` bits; and
2. the reference earns zero in expectation.

If rejection earns `F`, then
`p[-log2(p)] + (1-p)F = 0`, which forces
`F = p log2(p)/(1-p)`.

## 3. S20 probability representation

IWU-S20 represents `p_i` as an integer `reference_ticks` satisfying:

```text
1 <= reference_ticks < 2^20
p_i = reference_ticks / 2^20
```

An analytical probability is rounded to the nearest tick with
`floor(p × 2^20 + 0.5)`. Values that round to zero or `2^20` are invalid.

For empirical binary reference evidence, the default estimator is the
Krichevsky-Trofimov half-count:

```text
p_raw = (successes + 1/2) / (trials + 1)
```

`p_raw` is then quantized to S20. A conforming record MUST retain the integer
success and trial counts or declare that its ticks came from an analytical or
already compiled registry entry.

The point estimator does not eliminate reference-estimation uncertainty.

## 4. Workload registry

A conforming study MUST freeze before candidate outcomes are examined:

- the episode population or sampling policy;
- the task-to-stratum assignment rule;
- the automatic verifier and acceptance rule;
- the reference system or policy;
- reference evidence and S20 ticks for every stratum;
- the measured system configuration, including tools and retry policy; and
- the treatment of timeouts, missing outputs, and invalid outputs.

Registry, verifier, reference, and system identifiers SHOULD be content-addressed.
A label without immutable content is insufficient for an auditable comparison.

Reference selection is part of the estimand. A weak or selectively chosen
reference inflates IWU and invalidates comparisons with another reference.

## 5. Episode boundary

One episode is one assigned opportunity for the measured system to produce a
verified result.

- Acceptance MUST come from the frozen binary verifier.
- A timeout, missing output, invalid output, or verifier error MUST be rejected
  unless the registry declared another rule before evaluation.
- Internal retries MUST NOT create additional scored episodes.
- All calls, retries, tools, and evaluation resources inside the declared
  operating boundary MUST be accumulated on the episode.
- Every assigned episode MUST be retained. Dropping failures is nonconforming.

## 6. Core record

A conforming record contains:

| Field | Meaning |
|---|---|
| `schema` | Exact specification version |
| `episode_id` | Unique episode identifier |
| `system_id` | Complete measured system/policy identity |
| `block_id` | Declared independent sampling block |
| `registry_id` | Frozen workload registry identity |
| `stratum_id` | Predeclared task stratum |
| `verifier_id` | Frozen verifier identity |
| `reference_id` | Frozen reference policy/evidence identity |
| `reference_ticks` | Integer S20 reference probability |
| `reference_denominator` | Exactly `1048576` |
| `reference_source` | Tick, analytical, or KT-count provenance |
| `accepted` | Boolean verified outcome |
| `reference_probability` | `reference_ticks / 1048576` |
| `difficulty_bits` | `-log2(reference_probability)` |
| `iwu` | Episode score |
| `resources` | Non-negative numbers or `null` |
| `identity_sha256` | Hash of the integer/string/boolean core identity |

The normative JSON shape is in
[`schema/iwu-s20-record.schema.json`](schema/iwu-s20-record.schema.json).

Identifiers are Unicode NFC strings without surrounding whitespace. Counts and
ticks MUST be safe integers no greater than `2^53-1`, enabling equivalent Python
and JavaScript representations. The core hash does not commit floating-point
resource telemetry; production evidence systems MAY apply a stronger envelope
signature or content commitment.

## 7. Aggregation and comparison

Records MAY be summed only when these identities match exactly:

- specification version;
- system;
- workload registry;
- verifier; and
- reference.

Strata and reference ticks MAY differ within the same frozen registry. Duplicate
episode identifiers MUST be rejected.

Comparisons between systems require separate reports over the same registry,
verifier, reference, and sampling policy. Scores under different references do
not share a zero point and MUST NOT be ranked as if they did.

## 8. Resource ratios

Resource telemetry MUST NOT alter `IWU_i`. Over a complete ledger:

```text
IWU/resource = sum(IWU_i) / sum(resource_i)
```

Implementations MUST use the ratio of totals, not the mean of per-episode ratios.
If any episode is missing a requested resource, its aggregate and ratio MUST be
reported as unavailable. Zero resource does not imply infinite efficiency.

A signed point ratio is descriptive. An efficiency superiority claim SHOULD NOT
be made unless an appropriate uncertainty analysis supports a positive total.

## 9. Uncertainty

The point score is deterministic conditional on the registry and outcomes.
Inferential claims are not.

A public inferential report MUST disclose:

- reference sample sizes and estimation method;
- candidate sample size;
- the actual independent blocking unit;
- interval or testing procedure;
- whether reference-estimation uncertainty is included; and
- missingness and stopping rules.

Observation-level intervals MUST NOT be used when observations are dependent.
The bundled block bootstrap is explicitly limited to candidate sampling with the
reference ticks treated as fixed. It is not a complete interval when reference
probabilities were estimated from finite data. A joint block bootstrap, paired
design, hierarchical model, or other justified procedure SHOULD then propagate
both sources of uncertainty.

## 10. Conformance levels

### Core-conformant

- Implements Sections 2, 3, 5, 6, and 7.
- Produces the exact `+1` and `-1` fixtures at `p=1/2`.
- Passes the language-specific conformance tests.

### Study-conformant

- Is core-conformant.
- Publishes the frozen registry and evidence boundary.
- Retains all assigned episodes and complete declared resource telemetry.
- Reports uncertainty according to Section 9.

### Independently replicated

- Is study-conformant.
- Has been reproduced by an organization independent of the registry and
  implementation authors.

This repository currently demonstrates core conformance and author-run study
evidence. It does not claim independent replication.

## 11. Non-goals

IWU-S20 does not define:

- a universal benchmark;
- a universal reference system;
- an automatic verifier for subjective work;
- a scalar that combines dollars, energy, time, and outcomes;
- a replacement for accuracy, calibration, safety evaluation, or causal study;
- a thermodynamic energy lower bound; or
- a legal or academic novelty determination.

## 12. Security and gaming considerations

The main threats are registry selection after seeing results, weak references,
verifier exploitation, task leakage, duplicate or dropped episodes, hidden retry
costs, incorrect independence claims, and comparison across identities.

Conforming publications SHOULD release enough immutable metadata to detect these
failures without exposing private prompts or outputs. Sensitive deployments may
publish content hashes and aggregate evidence rather than raw data.
