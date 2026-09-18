"""IWU-S20 reference implementation.

IWU-S20 reports additive, reference-centered verified success surprisal.
The module has no third-party runtime dependencies.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import unicodedata
from collections import defaultdict
from typing import Any, Iterable, Mapping


SPEC_VERSION = "IWU-S20/0.2-draft"
SCALE_BITS = 20
SCALE = 1 << SCALE_BITS
MAX_SAFE_INTEGER = (1 << 53) - 1


class IWUError(ValueError):
    """Raised when an IWU-S20 input or record is invalid."""


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IWUError(f"{label} must be a non-empty string")
    normalized = unicodedata.normalize("NFC", value)
    if normalized != normalized.strip():
        raise IWUError(f"{label} must not have leading or trailing whitespace")
    return normalized


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise IWUError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise IWUError(f"{label} must be finite")
    return result


def _safe_integer(value: Any, label: str, *, minimum: int = 0) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < minimum
        or value > MAX_SAFE_INTEGER
    ):
        raise IWUError(
            f"{label} must be an integer in [{minimum},{MAX_SAFE_INTEGER}]"
        )
    return value


def probability_to_ticks(reference_probability: Any) -> int:
    """Quantize an analytical probability to the nearest S20 tick."""

    probability = _number(reference_probability, "reference_probability")
    if not 0.0 < probability < 1.0:
        raise IWUError("reference_probability must be strictly between zero and one")
    ticks = int(math.floor(probability * SCALE + 0.5))
    if not 1 <= ticks < SCALE:
        raise IWUError("reference_probability is outside the representable S20 range")
    return ticks


def resolve_reference(
    *,
    reference_ticks: int | None = None,
    reference_probability: float | None = None,
    reference_successes: int | None = None,
    reference_trials: int | None = None,
) -> dict[str, Any]:
    """Resolve exactly one S20 reference representation.

    Production registries should normally store ``reference_ticks``. Analytical
    probabilities and empirical counts are convenience inputs for registry
    construction and small integrations.
    """

    ticks_mode = reference_ticks is not None
    probability_mode = reference_probability is not None
    counts_mode = reference_successes is not None or reference_trials is not None
    if sum((ticks_mode, probability_mode, counts_mode)) != 1:
        raise IWUError(
            "provide exactly one of reference_ticks, reference_probability, "
            "or the reference_successes/reference_trials pair"
        )

    if ticks_mode:
        ticks = _safe_integer(reference_ticks, "reference_ticks", minimum=1)
        if ticks >= SCALE:
            raise IWUError(f"reference_ticks must be below {SCALE}")
        source = {"method": "s20_ticks"}
    elif probability_mode:
        ticks = probability_to_ticks(reference_probability)
        source = {"method": "analytical"}
    else:
        successes = _safe_integer(
            reference_successes, "reference_successes", minimum=0
        )
        trials = _safe_integer(reference_trials, "reference_trials", minimum=1)
        if successes > trials:
            raise IWUError("reference_successes must not exceed reference_trials")
        # Krichevsky-Trofimov half-count estimate.
        probability = (successes + 0.5) / (trials + 1.0)
        ticks = probability_to_ticks(probability)
        source = {
            "method": "krichevsky_trofimov",
            "successes": successes,
            "trials": trials,
        }

    return {
        "resolution_bits": SCALE_BITS,
        "reference_ticks": ticks,
        "reference_denominator": SCALE,
        "reference_probability": ticks / SCALE,
        "reference_source": source,
    }


def canonical_json(value: Any) -> str:
    """Canonical JSON for the integer/string/boolean core identity object."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def score_from_ticks(accepted: bool, reference_ticks: int) -> float:
    """Score one verified outcome against an S20 reference."""

    if not isinstance(accepted, bool):
        raise IWUError("accepted must be boolean")
    ticks = _safe_integer(reference_ticks, "reference_ticks", minimum=1)
    if ticks >= SCALE:
        raise IWUError(f"reference_ticks must be below {SCALE}")
    probability = ticks / SCALE
    difficulty_bits = -math.log2(probability)
    if accepted:
        return difficulty_bits
    return -(probability / (1.0 - probability)) * difficulty_bits


def score_from_probability(accepted: bool, reference_probability: float) -> float:
    """Convenience wrapper that first quantizes the probability to S20."""

    return score_from_ticks(accepted, probability_to_ticks(reference_probability))


def expected_iwu(treatment_probability: float, reference_ticks: int) -> float:
    """Expected IWU at treatment pass probability ``q`` and represented S20 ``p``."""

    treatment = _number(treatment_probability, "treatment_probability")
    if not 0.0 <= treatment <= 1.0:
        raise IWUError("treatment_probability must be in [0,1]")
    ticks = _safe_integer(reference_ticks, "reference_ticks", minimum=1)
    if ticks >= SCALE:
        raise IWUError(f"reference_ticks must be below {SCALE}")
    reference = ticks / SCALE
    return ((treatment - reference) / (1.0 - reference)) * (-math.log2(reference))


def _validated_resources(resources: Mapping[str, Any] | None) -> dict[str, float | None]:
    if resources is None:
        return {}
    if not isinstance(resources, Mapping):
        raise IWUError("resources must be an object")
    output: dict[str, float | None] = {}
    for raw_name, value in resources.items():
        name = _identifier(raw_name, "resource name")
        if name in output:
            raise IWUError(f"duplicate normalized resource name: {name}")
        if value is None:
            output[name] = None
            continue
        amount = _number(value, f"resources.{name}")
        if amount < 0.0:
            raise IWUError(f"resources.{name} must be non-negative")
        output[name] = amount
    return dict(sorted(output.items()))


def _core_identity(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return the exact, cross-language hash surface (no floats)."""

    return {
        "schema": record["schema"],
        "episode_id": record["episode_id"],
        "system_id": record["system_id"],
        "block_id": record["block_id"],
        "registry_id": record["registry_id"],
        "stratum_id": record["stratum_id"],
        "verifier_id": record["verifier_id"],
        "reference_id": record["reference_id"],
        "reference_ticks": record["reference_ticks"],
        "reference_source": record["reference_source"],
        "accepted": record["accepted"],
    }


def observe(
    *,
    episode_id: str,
    system_id: str,
    accepted: bool,
    registry_id: str,
    stratum_id: str,
    verifier_id: str,
    reference_id: str,
    block_id: str,
    reference_ticks: int | None = None,
    reference_probability: float | None = None,
    reference_successes: int | None = None,
    reference_trials: int | None = None,
    resources: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create one IWU-S20 record after automatic verification."""

    if not isinstance(accepted, bool):
        raise IWUError("accepted must be boolean")
    reference = resolve_reference(
        reference_ticks=reference_ticks,
        reference_probability=reference_probability,
        reference_successes=reference_successes,
        reference_trials=reference_trials,
    )
    record: dict[str, Any] = {
        "schema": SPEC_VERSION,
        "episode_id": _identifier(episode_id, "episode_id"),
        "system_id": _identifier(system_id, "system_id"),
        "block_id": _identifier(block_id, "block_id"),
        "registry_id": _identifier(registry_id, "registry_id"),
        "stratum_id": _identifier(stratum_id, "stratum_id"),
        "verifier_id": _identifier(verifier_id, "verifier_id"),
        "reference_id": _identifier(reference_id, "reference_id"),
        "reference_ticks": reference["reference_ticks"],
        "reference_denominator": SCALE,
        "reference_source": reference["reference_source"],
        "accepted": accepted,
    }
    record["identity_sha256"] = sha256_json(_core_identity(record))
    probability = reference["reference_probability"]
    record["reference_probability"] = probability
    record["difficulty_bits"] = -math.log2(probability)
    record["iwu"] = score_from_ticks(accepted, reference["reference_ticks"])
    record["resources"] = _validated_resources(resources)
    return record


def validate_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a record and return a normalized shallow copy."""

    if not isinstance(record, Mapping):
        raise IWUError("record must be an object")
    if record.get("schema") != SPEC_VERSION:
        raise IWUError(f"schema must equal {SPEC_VERSION}")

    output = dict(record)
    for field in (
        "episode_id",
        "system_id",
        "block_id",
        "registry_id",
        "stratum_id",
        "verifier_id",
        "reference_id",
    ):
        normalized = _identifier(output.get(field), field)
        if normalized != output[field]:
            raise IWUError(f"{field} must use NFC normalization")

    ticks = _safe_integer(output.get("reference_ticks"), "reference_ticks", minimum=1)
    if ticks >= SCALE or output.get("reference_denominator") != SCALE:
        raise IWUError("record is not an S20 probability representation")
    if not isinstance(output.get("accepted"), bool):
        raise IWUError("accepted must be boolean")

    source = output.get("reference_source")
    if not isinstance(source, Mapping):
        raise IWUError("reference_source must be an object")
    method = source.get("method")
    if method == "krichevsky_trofimov":
        if set(source) != {"method", "successes", "trials"}:
            raise IWUError("unsupported or malformed reference_source")
        resolved = resolve_reference(
            reference_successes=source.get("successes"),
            reference_trials=source.get("trials"),
        )
        if resolved["reference_ticks"] != ticks:
            raise IWUError("reference_source counts do not produce reference_ticks")
    elif method not in {"analytical", "s20_ticks"} or set(source) != {"method"}:
        raise IWUError("unsupported or malformed reference_source")

    probability = ticks / SCALE
    observed_probability = _number(output.get("reference_probability"), "reference_probability")
    if observed_probability != probability:
        raise IWUError("reference_probability does not match reference_ticks")
    difficulty = -math.log2(probability)
    if not math.isclose(
        _number(output.get("difficulty_bits"), "difficulty_bits"),
        difficulty,
        rel_tol=0.0,
        abs_tol=1e-15,
    ):
        raise IWUError("difficulty_bits does not match reference_ticks")
    expected_score = score_from_ticks(output["accepted"], ticks)
    if not math.isclose(
        _number(output.get("iwu"), "iwu"),
        expected_score,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise IWUError("iwu does not match the IWU-S20 formula")
    expected_hash = sha256_json(_core_identity(output))
    if output.get("identity_sha256") != expected_hash:
        raise IWUError("identity_sha256 does not match the core record")
    output["resources"] = _validated_resources(output.get("resources"))
    return output


def measure(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate comparable IWU-S20 records and resource telemetry."""

    if isinstance(records, (str, bytes, Mapping)):
        raise IWUError("records must be an iterable of objects")
    rows = [validate_record(record) for record in records]
    if not rows:
        raise IWUError("at least one record is required")

    seen: set[str] = set()
    for row in rows:
        episode_id = row["episode_id"]
        if episode_id in seen:
            raise IWUError(f"duplicate episode_id: {episode_id}")
        seen.add(episode_id)

    comparable_fields = (
        "schema",
        "system_id",
        "registry_id",
        "verifier_id",
        "reference_id",
    )
    for field in comparable_fields:
        if len({row[field] for row in rows}) != 1:
            raise IWUError(f"mixed {field} values must not be merged")

    total = math.fsum(row["iwu"] for row in rows)
    resource_names = sorted({name for row in rows for name in row["resources"]})
    resource_totals: dict[str, float | None] = {}
    iwu_per_resource: dict[str, float | None] = {}
    for name in resource_names:
        values = [row["resources"].get(name) for row in rows]
        if any(value is None for value in values):
            resource_totals[name] = None
            iwu_per_resource[name] = None
            continue
        amount = math.fsum(float(value) for value in values)
        resource_totals[name] = amount
        iwu_per_resource[name] = total / amount if amount > 0.0 else None

    return {
        "schema": SPEC_VERSION,
        "system_id": rows[0]["system_id"],
        "registry_id": rows[0]["registry_id"],
        "verifier_id": rows[0]["verifier_id"],
        "reference_id": rows[0]["reference_id"],
        "episode_count": len(rows),
        "block_count": len({row["block_id"] for row in rows}),
        "stratum_count": len({row["stratum_id"] for row in rows}),
        "accepted_count": sum(row["accepted"] for row in rows),
        "acceptance_rate": sum(row["accepted"] for row in rows) / len(rows),
        "iwu_total": total,
        "iwu_per_episode": total / len(rows),
        "resource_totals": resource_totals,
        "iwu_per_resource": iwu_per_resource,
    }


def block_bootstrap_interval(
    records: Iterable[Mapping[str, Any]],
    *,
    iterations: int = 2_000,
    confidence: float = 0.95,
    seed: int = 0,
) -> dict[str, Any]:
    """Fixed-reference interval from resampling declared independent blocks.

    This interval does not include uncertainty in estimated reference
    probabilities. Public inferential claims must handle that uncertainty from
    the underlying reference observations as well.
    """

    rows = [validate_record(record) for record in records]
    measure(rows)
    if isinstance(iterations, bool) or not isinstance(iterations, int) or iterations < 100:
        raise IWUError("iterations must be an integer of at least 100")
    confidence_value = _number(confidence, "confidence")
    if not 0.0 < confidence_value < 1.0:
        raise IWUError("confidence must be strictly between zero and one")

    blocks: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        blocks[row["block_id"]].append(row["iwu"])
    if len(blocks) < 2:
        raise IWUError("at least two declared independent blocks are required")

    values = list(blocks.values())
    rng = random.Random(seed)
    estimates: list[float] = []
    for _ in range(iterations):
        sampled = [values[rng.randrange(len(values))] for _ in values]
        count = sum(len(block) for block in sampled)
        estimates.append(math.fsum(value for block in sampled for value in block) / count)
    estimates.sort()
    alpha = (1.0 - confidence_value) / 2.0

    def quantile(probability: float) -> float:
        position = probability * (len(estimates) - 1)
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return estimates[lower]
        fraction = position - lower
        return estimates[lower] * (1.0 - fraction) + estimates[upper] * fraction

    return {
        "scope": "fixed_reference_candidate_blocks_only",
        "confidence": confidence_value,
        "iterations": iterations,
        "block_count": len(blocks),
        "point_iwu_per_episode": math.fsum(row["iwu"] for row in rows) / len(rows),
        "lower_iwu_per_episode": quantile(alpha),
        "upper_iwu_per_episode": quantile(1.0 - alpha),
        "reference_estimation_uncertainty_included": False,
    }
