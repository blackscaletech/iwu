# Data and evidence provenance

The raw retrospective source is excluded from the repository. Its canonical URL, pinned commit and SHA-256 are recorded in `sources/PROVENANCE.json`. The public source tree's dataset license was unresolved at the pinned revision. Researchers should establish applicable upstream rights before retrieval, reuse or redistribution.

The repository contains original numerical analyses and attributed summary outputs for methodological review. Original-contribution licenses apply only to rights held in those contributions. They provide no additional license to the underlying dataset or other upstream material.

| Evidence | Included | Purpose |
| --- | --- | --- |
| Raw upstream records and code | Excluded | Retrieved independently from the pinned upstream location. |
| Aggregate numerical results | Included | Inspect uncertainty, sensitivity and proxy-score calculations. |
| Per-task derived summaries | Included | Reproduce numerical checks and inspect workload concentration. |
| Original synthetic test fixtures | Included | Exercise the accounting and uncertainty implementations. |
| Sanitized live final answers and usage | Included | Re-score the instrumentation check and inspect available evidence. |
| Worker conversations and private reasoning | Excluded | Outside the evidence boundary. |
| Credentials, local paths and personal configuration | Excluded | Outside the publication boundary. |

Live records contain model configuration requests, final answers, available usage and sanitized event metadata. Original tool bodies and provider bills are unavailable. Their absence remains a certification limitation.

The original local protocol is identified by SHA-256 in the selection lock. The public methods account was prepared after analysis and makes no external preregistration claim. Portable source retrieval verifies the expected digest before persisting any bytes. The release manifest records digests for every included resource.
