"""Self-contained randomized mathematical gates for IWU-S20."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from iwu import SCALE, expected_iwu, score_from_ticks


def run(count: int = 100_000) -> dict[str, object]:
    rng = random.Random(20260918)
    max_zero_error = 0.0
    directional_failures = 0
    minimum = math.inf
    maximum = -math.inf
    for _ in range(count):
        ticks = rng.randrange(1, SCALE)
        probability = ticks / SCALE
        success = score_from_ticks(True, ticks)
        failure = score_from_ticks(False, ticks)
        max_zero_error = max(
            max_zero_error,
            abs(probability * success + (1 - probability) * failure),
        )
        treatment = rng.random()
        expectation = expected_iwu(treatment, ticks)
        if (
            (treatment > probability and not expectation > 0)
            or (treatment < probability and not expectation < 0)
            or (treatment == probability and expectation != 0)
        ):
            directional_failures += 1
        minimum = min(minimum, success, failure)
        maximum = max(maximum, success, failure)
    return {
        "candidate": "IWU-S20",
        "records": count,
        "directional_failures": directional_failures,
        "max_reference_zero_error": max_zero_error,
        "min_finite_iwu": minimum,
        "max_finite_iwu": maximum,
        "all_finite": math.isfinite(minimum) and math.isfinite(maximum),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()
    actual = run()
    if args.check:
        expected = json.loads(args.check.read_text())
        for key in ("candidate", "records", "directional_failures", "all_finite"):
            if actual[key] != expected[key]:
                raise SystemExit(f"{key} mismatch")
        for key in ("max_reference_zero_error", "min_finite_iwu", "max_finite_iwu"):
            if not math.isclose(actual[key], expected[key], rel_tol=0.0, abs_tol=1e-15):
                raise SystemExit(f"{key} mismatch")
    if actual["directional_failures"] or actual["max_reference_zero_error"] >= 1e-12:
        raise SystemExit("mathematical validation gate failed")
    print(json.dumps(actual, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
