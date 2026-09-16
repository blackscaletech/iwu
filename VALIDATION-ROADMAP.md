# What would make IWU credible as a standard candidate?

The current result is a prototype with useful failure findings. The next study must test measurement validity through human calibration and independent evidence.

## Stage 1 - independent human calibration

Start with a deliberately narrow registry: 30 tasks, 10 each in software maintenance, structured data analysis and evidence-based document extraction. Use fresh, licensed task variants; freeze inputs, acceptance and time budgets before any model trial. These domain labels describe the proposed next study.

Obtain at least 5 accepted timed expert completions per task, using independently recruited qualified workers and a balanced assignment plan. This minimum is a feasibility starting point. A power calculation requires pilot variance estimates. Record failures, censored time, expertise, allowed tools, setup, active task work and breaks. Do not present model-estimated or author-guessed durations as human measurements. Specify human compensation and privacy/consent before recruitment; no recruitment or payments have occurred.

Pre-register the expert-time estimand, treatment of censoring and precision criterion. A candidate release target is a 95% interval no wider than +/-20% of the point estimate for each task or its preregistered pooled stratum. This is a proposed engineering target requiring review. Use calibration-pilot variance to calculate the required human sample; retire or mark uncalibrated tasks that cannot support the target. Do not keep sampling only favorable items.

## Stage 2 - prospective cross-provider replication

Use at least three provider families and two independently implemented harnesses, with exact model versions, reasoning settings, tool policies and invoice-backed costs. Randomize/interleave conditions to reduce order and service-load confounding. Capture provider-reported identity or equivalent attestation. Separate a no-tool profile from a fixed-tool profile; changes define distinct systems and require new configuration identifiers.

Pre-register 10 independent episodes per task/system as a starting design; refine that number by power simulation from the calibration pilot. Include hard tasks, partial failures and real tool failures. Keep all assigned episodes in the disposition ledger. An independent team runs the second implementation and holds scoring keys.

Acceptance should be deterministic where possible. For open-ended outputs, use blinded human judgments, adjudicate disagreement, measure agreement with uncertainty, and compare at least two judge-model families only as secondary tools. A judge-model score is not a gold standard just because the judge is powerful.

## Stage 3 - try to falsify the metric

Test decomposition inflation, hidden retries, cached prior answers, duplicate charges, future-context leakage, model fallback, missing outputs, ambiguous baselines and invoice/trace mismatches. Verify that all intentional faults are either detected or explicitly outside the audit boundary.

Measure stability of both **levels and rankings** under held-out workload shifts, alternate expertise cohorts and permitted human tools. Test whether IWU and full-cost efficiency predict independently measured buyer outcomes better than acceptance alone and cost per accepted task. Do not assume prediction of labor savings; measure that separately in a randomized productivity study.

Publish task-, family-, trial-, calibration- and judge-uncertainty components. Declare minimum detectable differences and avoid “winner” claims when relevant paired intervals include zero. Prospective interoperability target: two independent implementations agree to relative tolerance 1e-9 on valid golden ledgers and reject every published malformed fixture. External audit remains necessary for completeness.

## Stage 4 - governance and independent adoption

Invite evaluators, model providers, buyers and measurement researchers to review a public RFC. Establish versioning, conflicts-of-interest disclosure, registry stewardship, audit appeals, privacy rules and an explicit license. Keep the calibration registry separate from any provider's product. Require at least two independent implementations and a public replication before proposing a 1.0 profile.

Standards development requires open governance, independent implementation and adoption. Research claims and limitations should remain attached to versioned releases and public methodological review.
