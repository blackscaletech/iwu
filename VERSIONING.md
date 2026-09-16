# Versioning and compatibility

The reference implementation follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html). `VERSION` is the release version. Python metadata uses the equivalent PEP 440 representation: `0.1.0-rc.1` maps to `0.1.0rc1`.

The public API comprises `iwu.calculate`, `iwu.canonical_hash`, `iwu.InvalidLedger`, `trace_audit.audit`, `trace_audit.credit_atoms`, and the three interval functions in `uncertainty.py`, including their documented input and output contracts.

During `0.x` development, incompatible API changes increment the minor version. Compatible fixes increment the patch version. Release candidates use `-rc.N`. A stable `1.0.0` release requires a declared compatibility commitment and independent implementation review.

Scientific identity is separate:

- Specification drafts carry their own revision.
- Workload registries are immutable and identified by content hashes.
- Source datasets retain exact upstream commits and byte digests.
- Changes to calibration, acceptance or workload composition create a new profile or registry identity.

Each release uses an annotated `vMAJOR.MINOR.PATCH[-rc.N]` tag and a matching changelog entry. Published tags and assets are immutable. Corrections receive a new version with a description of their impact on prior results.

CI validates versions, tests, permitted repository contents, artifact hashes and commit identities. Release artifacts include a SHA-256 manifest. Registry versions remain embedded in score records.
