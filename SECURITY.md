# Security policy

The current research-preview line receives maintenance from @blackscaletech. Security support is limited to the documented input-validation and publication-boundary checks.

Use GitHub private vulnerability reporting when it is available for this repository. Otherwise request a private reporting channel from the maintainer without posting exploit details, credentials or private research records publicly. Report the affected version, a minimal sanitized reproducer and the expected impact.

The calculator checks declared records. A deployment still requires trusted capture, input isolation, resource limits and appropriate handling of sensitive tool evidence. Treat imported ledgers, traces and artifacts as untrusted data. The live harness is an explicit opt-in research utility that invokes local model tooling and may incur usage charges.

The release content check scans source, documents, PDF metadata/text, decoded fixture payloads and committed history for forbidden file classes and common credential or machine-path patterns. This is a defense-in-depth control with a documented scope. Secret rotation and incident review remain necessary if exposure is suspected.
