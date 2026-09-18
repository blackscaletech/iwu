# Validation evidence

This directory separates reproducible core checks from broader author-run
evidence.

- `VALIDATION-PROTOCOL.md` is the falsification protocol locked before the first S20
  implementation.
- `PROTOCOL-LOCK.json` records its SHA-256 commitment.
- `MATH-RESULTS.json` is reproduced by `tools/validate_math.py`.
- `CROSS-LANGUAGE-RESULTS.json` is reproduced independently by the Python and
  JavaScript crosscheck programs.
- `AUTHOR-RESULTS.json` contains the original broader holdout, sensitivity,
  dependence, and structured-inference results.

The public implementation was hardened after the locked experiment by fixing the
resolution to S20 and adding system/stratum identities plus strict record
validation. These changes do not alter the episode formula or the recorded
holdout scores. The broader holdout depends on frozen episode ledgers from the
research workspace and is therefore preserved as author-run evidence rather than
presented as a self-contained independent replication.

See [`../VALIDATION.md`](../VALIDATION.md) for claim boundaries and proposed
external falsification work.
