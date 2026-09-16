# Reproduction guide

## Offline verification

```sh
python -m unittest discover -s tests -v
python scripts/example.py
python tools/check_recorded_evidence.py
```

The suite uses the standard library. It checks 60 conformance methods. Recorded-answer verification independently re-scores 12 keys and 72 final answers. Executing these commands performs zero new model calls.

Install `.[qa]` for PDF and release-integrity checks, then run:

```sh
python tools/check_release.py --history
```

## Optional retrospective reanalysis

Install `.[analysis]`. Review [DATA.md](DATA.md) before retrieving the upstream file.

```sh
python scripts/fetch_source.py
python scripts/analyze_public.py
python scripts/verify_reproduction.py
```

The public fetcher verifies the immutable source hash before writing the raw file. Git ignores that file. The analysis recomputes the locked selection and task/family intervals. The reproduction check repeats the analysis twice and checks byte-identical deterministic numerical outputs in the tested environment. Generated outputs may replace derived result files; use a fresh checkout for each reproduction.

The private operational protocol remains represented by its original hash commitment. Public methods are a post-analysis account. Source identity and selection gates remain enforced in the portable analysis entry point.

## Synthetic checks

```sh
python scripts/red_team.py
python scripts/test_corrected_uncertainty.py
```

The red-team script includes a retrospective extension and requires the retrieved source file. The corrected-uncertainty suite is fully synthetic. It evaluates 12,000 experiments under recorded integer seeds. The resulting simulations measure coverage for their declared designs.

## Live inference

The archived smoke test requested `gpt-5.6-sol` / `medium`. `scripts/live_smoke.py` exposes the prospective harness for a separately identified study. It requires compatible authenticated tooling and can consume account usage. Its original flags and model route are recorded research configuration; current availability needs a fresh capability check.

The harness refuses to overwrite existing live results. Plan a new study identifier, permitted tools, human calibration and capture requirements before using it. Preserve every attempted run and disclose effective identity and evidence gaps.

## Paper typesetting

Install `.[paper]` and provide a separately licensed Helvetica Neue TTC through `IWU_FONT_TTC`:

```sh
export IWU_FONT_TTC=/path/to/licensed/HelveticaNeue.ttc
python scripts/build_brief.py
```

The builder produces only the research paper in this repository. Formulas use STIX vector outlines. A4 geometry, the Swarm header, Swarm Research front matter and swarm.services footer follow the research publication format. Embedded font subsets support display; font source files are excluded.

## Environment and scope

The recorded deterministic reexecutions used Python 3.12 and NumPy 2.3.5. CI checks Python 3.12 and 3.13 when run by GitHub. Cross-platform validation and independent reproduction remain empirical questions. A passing local suite establishes the checks performed in that environment.
