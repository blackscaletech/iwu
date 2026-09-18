# IWU-S20 validation status

IWU-S20 is a mathematically checked and cross-language tested standard candidate.
The evidence is author-run and has not yet been independently replicated.

## What has passed

- **100,000 randomized mathematical cases:** zero directional-sign failures,
  maximum reference-centering error `1.11e-16`, and finite S20 boundary scores.
- **100,000 deterministic cross-language records:** identical Python and
  JavaScript episode scores and core identity commitments.
- **67,164 frozen holdout episodes in 57 groups:** included language-model and
  random-forest workloads; rank correlation with raw delta utility was `0.9441`.
- **Estimator sensitivity:** KT versus Laplace rank correlation was `0.9957`;
  KT versus direct B12/B16/B20 ranks were `0.985–0.987`.
- **Dependence stress test:** at simulated intra-block correlation `0.2`, naive
  observation-level 95% coverage fell to `57.65%`, while block-level coverage was
  `94.90%` across 10,000 simulations.
- **Non-LLM exercise:** the same formula and record shape processed structured
  inference and random-forest outcomes without a tokenizer or model-family term.
- **Current conformance suite:** 21 Python and 12 JavaScript tests cover the unit,
  centering, direction, fixed S20 representation, additivity, identity isolation,
  record tampering, resource completeness, Unicode normalization, and block
  interval scope.

The frozen protocol and detailed author-run results are in [`validation/`](validation/).

## What these results establish

They establish that the proposed score:

- is internally coherent under its stated axioms;
- has the intended zero and directional behavior;
- is implementable deterministically in two common languages;
- is different from token counts and unweighted success deltas; and
- can be applied without an LLM-specific input.

## What they do not establish

They do not establish that:

- IWU-S20 is already an industry or consensus standard;
- the axioms are the only socially useful choice;
- a particular verifier or reference registry is valid;
- finite reference probabilities are known without uncertainty;
- the holdout is representative of all inference workloads;
- IWU causes better operational or economic decisions; or
- the synthesis is legally or academically novel.

The holdout result is retrospective. The structured-inference exercise was small
and illustrative. The dependence simulation demonstrates why block handling
matters; it is not universal coverage proof for arbitrary data-generating
processes.

## Critical falsification targets

Independent reviewers should try to disprove the candidate by testing:

1. **Reference instability:** vary reference estimates within justified
   uncertainty and measure score/rank changes.
2. **Registry gaming:** quantify how much a weak but superficially plausible
   reference can inflate reported IWU.
3. **Stratum sensitivity:** merge and split predeclared strata without inspecting
   treatment outcomes, then test stability.
4. **Verifier validity:** compare automatic acceptance with downstream real-world
   outcomes on workloads where both exist.
5. **Decision value:** test whether IWU/resource selects better systems than
   tokens, cost, accuracy, and delta accuracy on sealed prospective deployments.
6. **Independent implementation:** reproduce the specification without importing
   this repository's code, then run the common fixtures.

## Release claim

The defensible claim is:

> IWU-S20 is an author-validated open standard candidate for additive,
> reference-centered verified inference work in bits. It now requires independent
> replication, prospective decision-value studies, and an open consensus process.

Stronger claims should wait for that evidence.
