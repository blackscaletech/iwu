# Prior art and the defensible contribution

Literature review conducted 15 September 2026. This targeted review supplies related-work context. Systematic priority assessment and legal review remain outside its scope.

| Primary source | Existing idea | How this draft relates |
| --- | --- | --- |
| [METR, Measuring AI Ability to Complete Long Tasks](https://arxiv.org/abs/2503.14499) and [public analysis](https://github.com/METR/eval-analysis-public) | Human task duration anchors agent evaluation. | IWU uses frozen reference effort as additive accepted-deliverable credit. Human-time grounding is established prior work. |
| [Kapoor et al., AI Agents That Matter, 2024](https://arxiv.org/abs/2407.01502) | Joint cost/accuracy evaluation and reproducible agent benchmarking. | Failed retries, total episode costs and efficiency frontiers are established accounting concerns. |
| [Truong et al., Reliable and Efficient Amortized Model-Based Evaluation](https://crfm.stanford.edu/2025/06/04/reliable-and-efficient-evaluation.html) | Rasch/IRT calibration and adaptive model evaluation. | A difficulty ladder can complement IWU. It should not be mislabeled as a ratio-scale quantity of useful work. |
| [Liu et al., BRIDGE, 2026](https://arxiv.org/abs/2602.07267) | Links a psychometric difficulty scale learned from model responses to human task time. | Especially close to the proposed overlapping-problem ladder. IWU cannot claim that mapping model performance to human duration is new. Predicted baselines still need uncertainty and held-out validation. |
| [Zhu, The Price of Intelligence, 2026 preprint](https://arxiv.org/abs/2608.29843) | Quality-adjusted AI price indices; token prices and task-level costs can diverge. | Strong close prior art. Rank stability does not establish metric-level stability. Quality-adjusted inference pricing is established prior work. |
| [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/) | Standardized model, agent, tool and usage telemetry. | Reuse existing observability infrastructure; add workload, verification, calibration and disjoint-cost commitments. |
| [NIST AI measurement and evaluation](https://www.nist.gov/ai-measurement-and-evaluation) and [measurement uncertainty](https://www.nist.gov/itl/sed/topic-areas/measurement-uncertainty) | Context-dependent evaluation and explicit uncertainty. | Relevant measurement principles. NIST validation and IWU compliance certification remain unclaimed. |
| [Basu, Cognitive Horsepower, working framework](https://signalfidelitygroup.com/insights/cognitive-horsepower) | Cost per approved output, review burden and verified useful throughput. | Related practical proposal with separate adoption and validation questions. |
| [The Joule Index, project proposal](https://joule.blankline.org/) | Auditable agent task cost and energy measurement. | A related implementation direction; vendor/project claims are not independently validated here. |

## Contribution being proposed

The prospective contribution is an explicit **reference-work interchange and accounting profile**: a named E60 anchor, immutable workload weights, independently accepted deliverables, conserved decomposition credit, intention-to-test missingness handling, complete episode-cost boundaries, trace provenance, conformance fixtures, and a transparent small feasibility study.

These ingredients draw on established measurement, evaluation and observability ideas. Their packaging and implementation may be useful. Priority, patentability and comparative superiority require separate investigation. Peer review should evaluate simplifications and identify existing standards the proposal could extend.
