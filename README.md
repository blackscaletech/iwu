# IWU: Inference Work Units

Swarm Research · [swarm.services](https://swarm.services)

IWU is a research specification and reference implementation for accounting for verified AI work on a defined workload. It combines frozen task probabilities, reference-expert effort and independently verified acceptance outcomes.

The first reference profile is **IWU-E60**: one unit credits **60 active reference-expert seconds** to an accepted deliverable. The profile identifier remains part of every score, alongside its workload, system configuration and operating boundary.

This repository provides the calculator, structural trace checks, uncertainty bounds, tests, study methods and reproducibility resources. Research preview: **v0.1.0-rc.1**, specification draft **0.1**. Human calibration, trace completeness and external validity remain explicit research requirements.

## Start here

| Resource | Purpose |
| --- | --- |
| [Research paper](output/pdf/IWU-RESEARCH-BRIEF.pdf) | Definition, pilot evidence, corrected uncertainty and limitations. |
| [Specification](SPECIFICATION.md) | Normative calculation, calibration and evidence requirements. |
| [Methods](docs/METHODS.md) | Study design, source selection, seeds and reproducibility boundaries. |
| [Results](RESULTS.md) and [machine-readable metrics](METRICS.json) | Recorded findings with uncertainty and provenance. |
| [Uncertainty correction](UNCERTAINTY-CORRECTION.md) | Fixed-registry bounds and synthetic failure-case tests. |
| [Examples](examples/) and [API guide](docs/API.md) | Small fixtures for adapting the calculator to another workload. |
| [Reproduction guide](docs/REPRODUCIBILITY.md) | Offline checks, optional source retrieval and deterministic reanalysis. |

## Quick start

Python 3.12 or newer is required. The three core modules and their 60-test conformance suite use the standard library.

```sh
python -m unittest discover -s tests -v
python scripts/example.py
```

For an editable installation and the optional numerical-analysis dependencies:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[analysis]'
```

On Windows, activate the environment with `.venv\Scripts\Activate.ps1` in PowerShell.

The example loads the included registry, assignment manifest and episode ledger, verifies their commitments, and prints the calculated work and cost fields. Every field is documented in [the API guide](docs/API.md).

## Calculation

For task probabilities `pi_i`, reference minutes `h_i`, and acceptance rates `p_hat_i` averaged over scheduled episodes:

```text
W_hat = sum_i(pi_i * h_i * p_hat_i)
```

The score is estimated IWU-E60 credit per assigned task. Unknown outcomes produce identified bounds. Internal retries belong to their assigned episode; their costs remain in the declared cost boundary. Full-cost efficiency uses the ratio of workload-weighted mean credit to complete mean cost.

The conservative one-sided confidence floor is:

```text
IWU-L95 = max(0, W_minus - sqrt(ln(20) * sum_g(B_g^2) / 2))
```

`W_minus` is observed accepted credit. `B_g` is the maximum contribution of independent block `g`; correlated observations share a block. The bound targets expected fixed-registry credit under fixed truthful weights, independent blocks and a fixed sample plan. Calibration error, judge error and changing workloads require additional uncertainty treatment.

## What the pilot tested

- 60 conformance test methods, including 3,000 deterministic randomized cases.
- 5,293 historical records across 170 common task IDs, with 10,000 paired task-bootstrap resamples.
- Six live smoke sessions on 12 reused deterministic tasks, yielding 72 accepted answers.
- 12,000 additional synthetic experiments for the corrected uncertainty rule.

The recorded live configuration requested `gpt-5.6-sol` at medium reasoning effort. Effective-model attestation was unavailable. Historical scores are reference-minute proxies; the live battery has a ceiling effect and lacks human timing calibration. Independent calibration and full trace audits remain necessary for audited work measurement. [Results](RESULTS.md) document all limitations and supplemental analyses.

## Reproduction and data

Offline tests and rescoring use the included fixtures and sanitized recorded outputs. The raw METR dataset is excluded. Its immutable revision, URL and SHA-256 appear in [source provenance](sources/PROVENANCE.json). Optional retrieval requires a separate network request to the upstream source; see [data provenance](docs/DATA.md).

The default CI performs offline tests and publication-boundary checks. Live inference is an explicit opt-in workflow with usage costs. Instructions for isolated reproduction and paper typesetting are in the reproduction guide.

## Versioning, citation and licensing

Software releases follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Registry hashes and scientific dataset revisions are separate immutable identifiers. [VERSIONING.md](VERSIONING.md) defines compatibility, and [CHANGELOG.md](CHANGELOG.md) records changes.

Use [CITATION.cff](CITATION.cff) to cite the reference implementation and paper. Maintainer: [@blackscaletech](https://github.com/blackscaletech).

Original code and executable fixtures use the [MIT license](LICENSE). Original research text, figures, paper and analytical contributions use [CC BY 4.0](LICENSES/CC-BY-4.0.txt). [LICENSES.md](LICENSES.md) defines scope, attribution and third-party exclusions. Swarm branding retains its applicable trademark rights.
