# IWU-S20

IWU-S20 is an open standard candidate for reporting **verified inference work
beyond a frozen reference**, in bits.

It complements tokens, dollars, joules, and latency. Those fields measure
resources. IWU-S20 measures whether an inference episode produced a verified
result, adjusted for how often a declared reference system succeeds on the same
kind of task.

> **Status:** author-validated draft for research and independent replication.
> It is not yet a consensus or industry standard.

## The unit

For one episode:

```text
IWU = ((accepted - p) / (1 - p)) × -log2(p)
```

- `accepted` is `1` or `0` from a frozen automatic verifier.
- `p` is the frozen reference pass probability for the episode's declared task
  stratum.
- `p` is represented as an integer number of ticks out of `2^20`; this is the
  `S20` profile.

One IWU is one bit of reference-centered verified success surprisal. A reference
system averages zero. A candidate has positive expected IWU exactly when its pass
probability is higher than the reference.

| Reference pass rate | Accepted episode | Rejected episode |
|---:|---:|---:|
| 50% | +1.000 IWU | -1.000 IWU |
| 25% | +2.000 IWU | -0.667 IWU |
| 10% | +3.322 IWU | -0.369 IWU |
| 90% | +0.152 IWU | -1.368 IWU |

## Five-minute integration

The reference implementations have no runtime dependencies. Copy `iwu.py` or
`iwu.mjs`, or install the Python project locally.

```python
from iwu import observe, measure

row = observe(
    episode_id="request-42",
    system_id="support-agent-v4@sha256:...",
    accepted=automatic_verifier(output),
    registry_id="support-workload-v1@sha256:...",
    stratum_id="billing/en/email",
    verifier_id="resolved-v3@sha256:...",
    reference_id="production-v1@sha256:...",
    block_id="customer-17",
    reference_successes=73,
    reference_trials=100,
    resources={
        "input_tokens": 1430,
        "latency_ms": 920,
        "cost_usd": 0.0031,
        "energy_joules": None,
    },
)

report = measure([row, *more_rows])
```

For production, compile reference evidence to `reference_ticks` once and store it
in a frozen registry. Passing counts at runtime is a convenience, not a reason to
re-estimate the baseline continuously.

The JavaScript API is equivalent:

```javascript
import { observe, measure } from "./iwu.mjs";

const row = observe({
  episodeId: "request-42",
  systemId: "support-agent-v4@sha256:...",
  accepted: automaticVerifier(output),
  registryId: "support-workload-v1@sha256:...",
  stratumId: "billing/en/email",
  verifierId: "resolved-v3@sha256:...",
  referenceId: "production-v1@sha256:...",
  blockId: "customer-17",
  referenceSuccesses: 73,
  referenceTrials: 100,
  resources: { input_tokens: 1430, latency_ms: 920, cost_usd: 0.0031 },
});

const report = measure([row, ...moreRows]);
```

See [the Python example](examples/python_example.py) and
[the JavaScript example](examples/javascript_example.mjs).

## What engineers report

Keep IWU separate from resources, then form ratios over a complete ledger:

```text
IWU per dollar = total IWU / total cost
IWU per joule  = total IWU / total energy
IWU per second = total IWU / total latency
IWU per token  = total IWU / total tokens
```

A missing resource value is `null`, never zero. A retry does not create a new
scored episode: include all retry resources in the original episode and score its
final verified outcome once.

## When records are comparable

Only merge records with the same:

- workload registry;
- automatic verifier;
- reference policy and evidence;
- measured system, including its tool and retry policy; and
- IWU-S20 specification version.

Different task strata may coexist inside that frozen registry. `measure()` rejects
mixed comparison identities, duplicate episodes, invalid resources, and modified
core records.

## What IWU-S20 does not solve

- It cannot make a subjective or weak verifier objective.
- It can be gamed by choosing an artificially weak reference; references must be
  canonical, frozen, versioned, and disclosed.
- Its zero point is reference-relative, so scores under different registries or
  references are not interchangeable.
- A point score is not a confidence claim. Estimated reference probabilities and
  dependent episodes require appropriate statistical treatment.
- It is a measurement convention for verified outcomes, not a universal measure
  of intelligence, semantic quality, or physical computation.

These restrictions are part of the standard, not optional caveats.

## Repository map

- [SPECIFICATION.md](SPECIFICATION.md) — normative definition and conformance.
- [VALIDATION.md](VALIDATION.md) — evidence, limitations, and replication targets.
- [`iwu.py`](iwu.py) and [`iwu.mjs`](iwu.mjs) — zero-dependency references.
- [`schema/`](schema/) — machine-readable episode schema.
- [`tests/`](tests/) and [`tools/`](tools/) — conformance and randomized checks.
- [`validation/`](validation/) — locked protocol and author-run results.

## Verify locally

```bash
python3 -m unittest discover -s tests -v
node --test tests/test_iwu.mjs
python3 tools/validate_math.py --check validation/MATH-RESULTS.json
python3 tools/crosscheck_fixture.py --check validation/CROSS-LANGUAGE-RESULTS.json
node tools/crosscheck.mjs --check validation/CROSS-LANGUAGE-RESULTS.json
```

## License and citation

Code and documentation are MIT licensed. See [CITATION.cff](CITATION.cff) for
citation metadata. Maintainer and initial author:
[@blackscaletech](https://github.com/blackscaletech).
