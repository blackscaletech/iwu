"""Minimal IWU-S20 integration example."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from iwu import measure, observe


def verifier(output: dict[str, bool]) -> bool:
    return output.get("resolved") is True


def main() -> None:
    outputs = [{"resolved": True}, {"resolved": False}, {"resolved": True}]
    costs = [0.0031, 0.0028, 0.0033]
    records = []
    for index, (output, cost) in enumerate(zip(outputs, costs, strict=True), start=1):
        records.append(
            observe(
                episode_id=f"request-{index}",
                system_id="support-agent-v4@sha256:demo",
                accepted=verifier(output),
                registry_id="support-workload-v1@sha256:demo",
                stratum_id="billing/en/email",
                verifier_id="resolved-v3@sha256:demo",
                reference_id="production-v1@sha256:demo",
                block_id=f"customer-{index}",
                reference_successes=73,
                reference_trials=100,
                resources={"cost_usd": cost, "input_tokens": 1400 + index * 10},
            )
        )

    print(measure(records))


if __name__ == "__main__":
    main()
