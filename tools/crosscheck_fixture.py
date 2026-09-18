"""Deterministic 100,000-record Python cross-language fixture."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from iwu import observe


def lcg(state: int) -> int:
    return (1664525 * state + 1013904223) & 0xFFFFFFFF


def run(count: int = 100_000) -> dict[str, object]:
    state = 0x5A17C0DE
    total = 0.0
    minimum = math.inf
    maximum = -math.inf
    hash_xor = 0
    for index in range(count):
        state = lcg(state)
        trials = 1 + state % 10_000
        state = lcg(state)
        successes = state % (trials + 1)
        state = lcg(state)
        accepted = bool(state & 1)
        row = observe(
            episode_id=f"random-{index}",
            system_id="system:crosscheck:v1",
            accepted=accepted,
            registry_id="registry:crosscheck:v1",
            stratum_id=f"counts:{successes}:{trials}",
            verifier_id="verifier:binary:v1",
            reference_id="reference:kt:v1",
            block_id=f"random-{index}",
            reference_successes=successes,
            reference_trials=trials,
        )
        total += row["iwu"]
        minimum = min(minimum, row["iwu"])
        maximum = max(maximum, row["iwu"])
        hash_xor ^= int(row["identity_sha256"][:16], 16)
    return {
        "count": count,
        "identity_hash_prefix_xor_hex": f"{hash_xor:016x}",
        "max_iwu": maximum,
        "mean_iwu": total / count,
        "min_iwu": minimum,
        "total_iwu": total,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()
    actual = run()
    if args.check:
        expected = json.loads(args.check.read_text())
        if actual["count"] != expected["count"]:
            raise SystemExit("count mismatch")
        if actual["identity_hash_prefix_xor_hex"] != expected["identity_hash_prefix_xor_hex"]:
            raise SystemExit("identity hash mismatch")
        for key in ("total_iwu", "mean_iwu", "min_iwu", "max_iwu"):
            if not math.isclose(actual[key], expected[key], rel_tol=0.0, abs_tol=1e-11):
                raise SystemExit(f"{key} mismatch")
    print(json.dumps(actual, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
