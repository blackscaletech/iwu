# Reference API

## Work accounting

```python
from iwu import calculate, canonical_hash, InvalidLedger
result = calculate(registry, assignments, ledger)
```

`registry` declares `unit: IWU-E60`, workload ID, registry version and tasks. Each task supplies a unique ID, positive workload probability, positive reference minutes and declared calibration status. Probabilities sum to one.

`assignments` commits to the registry hash and system ID and lists all scheduled episode/task pairs. `ledger` uses the same commitments, declares currency and cost boundary, and supplies observed episodes. Episodes contain a disposition (`accepted`, `rejected`, `unknown`), completeness flag, evidence hashes and disjoint primitive charges. Missing assigned episodes remain unknown.

Important outputs:

| Field | Interpretation |
| --- | --- |
| `work_per_assignment` | Estimated work for complete observed outcomes; otherwise `None`. |
| `work_bounds` | Identified lower and upper work bounds from missingness. |
| `outcome_coverage` | Workload-weighted observed-outcome coverage. |
| `full_cost_per_assignment` | Complete mean cost; otherwise `None`. |
| `work_per_currency_unit` | Ratio of mean work to complete positive mean cost; otherwise `None`. |
| `per_task` | Scheduled counts, acceptance bounds and cost completeness. |

Invalid declared records raise `InvalidLedger`, a `ValueError` subclass. `canonical_hash` uses the documented Python sorted-JSON encoding. Portable interchange requires agreement on canonical bytes.

## Trace consistency

```python
from trace_audit import audit, credit_atoms
report = audit(trace, artifact_bytes)
credit = credit_atoms(reference_minutes, atoms)
```

`audit` checks declared model/effort identity, allowed tools, input commitments, artifact contents, parent/predecessor order, timestamps and forbidden context. `artifact_bytes` maps SHA-256 strings to bytes. `credit_atoms` conserves the parent's reference credit across prespecified positive fractions summing to one.

## Uncertainty

```python
from uncertainty import bounded_sum_interval, lower_confidence_credit
interval = bounded_sum_interval(estimate, block_ranges, alpha=0.05)
lower = lower_confidence_credit(observed_lower, block_ranges, alpha=0.05)
```

Each range is the maximum possible contribution of one independent bounded block. Dependent observations share a block. `lower_confidence_credit` returns the lower credit, margin, confidence level, block count, maximum credit and interpretation. `incomplete_outcome_interval` combines identified outcome bounds with the two-sided sampling bound.

Calibration and future-workload uncertainty need separate treatment. Fixed-sample bounds require a valid sequential or multiplicity correction for adaptive selection or repeated peeking.

The fixtures in `examples/` provide complete working inputs. `scripts/example.py` verifies their exact expected score and decoded artifact commitments.
