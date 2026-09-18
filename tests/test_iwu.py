from __future__ import annotations

import math
import unittest

from iwu import (
    IWUError,
    SCALE,
    block_bootstrap_interval,
    expected_iwu,
    measure,
    observe,
    probability_to_ticks,
    resolve_reference,
    score_from_ticks,
    validate_record,
)


COMMON = {
    "system_id": "system:test:v1",
    "registry_id": "registry:test:v1",
    "stratum_id": "stratum:test:v1",
    "verifier_id": "verifier:test:v1",
    "reference_id": "reference:test:v1",
}


def record(episode_id: str, accepted: bool, probability: float = 0.5, **kwargs):
    block_id = kwargs.pop("block_id", episode_id)
    parameters = {**COMMON, **kwargs}
    return observe(
        episode_id=episode_id,
        accepted=accepted,
        block_id=block_id,
        reference_probability=probability,
        **parameters,
    )


class IWUS20Tests(unittest.TestCase):
    def test_unit_at_even_reference(self):
        self.assertEqual(record("success", True)["iwu"], 1.0)
        self.assertEqual(record("failure", False)["iwu"], -1.0)

    def test_reference_expectation_is_zero(self):
        for ticks in range(1, SCALE, 997):
            probability = ticks / SCALE
            success = score_from_ticks(True, ticks)
            failure = score_from_ticks(False, ticks)
            self.assertAlmostEqual(
                probability * success + (1 - probability) * failure,
                0.0,
                places=13,
            )

    def test_expected_sign_tracks_uplift(self):
        ticks = probability_to_ticks(0.3)
        represented = ticks / SCALE
        self.assertGreater(expected_iwu(represented + 0.1, ticks), 0)
        self.assertEqual(expected_iwu(represented, ticks), 0)
        self.assertLess(expected_iwu(represented - 0.1, ticks), 0)

    def test_rare_success_earns_more(self):
        hard = record("hard", True, 0.01)["iwu"]
        easy = record("easy", True, 0.5)["iwu"]
        self.assertGreater(hard, easy)

    def test_kt_estimator_has_finite_boundaries(self):
        zero = resolve_reference(reference_successes=0, reference_trials=128)
        one = resolve_reference(reference_successes=128, reference_trials=128)
        self.assertGreater(zero["reference_ticks"], 0)
        self.assertLess(one["reference_ticks"], SCALE)

    def test_all_reference_modes(self):
        ticks = probability_to_ticks(0.25)
        self.assertEqual(resolve_reference(reference_ticks=ticks)["reference_ticks"], ticks)
        self.assertEqual(
            resolve_reference(reference_probability=0.25)["reference_ticks"],
            ticks,
        )
        empirical = resolve_reference(reference_successes=0, reference_trials=1)
        self.assertEqual(empirical["reference_ticks"], ticks)

    def test_exactly_one_reference_mode_required(self):
        with self.assertRaisesRegex(IWUError, "exactly one"):
            resolve_reference()
        with self.assertRaisesRegex(IWUError, "exactly one"):
            resolve_reference(reference_ticks=1, reference_probability=0.5)
        with self.assertRaises(IWUError):
            resolve_reference(reference_successes=1)

    def test_additivity_and_duplication(self):
        records = [record("a", True, 0.25), record("b", False, 0.75)]
        result = measure(records)
        self.assertAlmostEqual(result["iwu_total"], math.fsum(row["iwu"] for row in records))
        duplicated = [
            records[0],
            records[1],
            record("c", True, 0.25),
            record("d", False, 0.75),
        ]
        doubled = measure(duplicated)
        self.assertAlmostEqual(doubled["iwu_total"], 2 * result["iwu_total"])
        self.assertAlmostEqual(doubled["iwu_per_episode"], result["iwu_per_episode"])

    def test_strata_may_differ_within_one_frozen_registry(self):
        easy = record("easy", True, 0.8, stratum_id="easy")
        hard = record("hard", True, 0.2, stratum_id="hard")
        report = measure([easy, hard])
        self.assertEqual(report["stratum_count"], 2)

    def test_resources_are_separate(self):
        one = record("a", True, 0.25, resources={"tokens": 1})
        two = record("b", True, 0.25, resources={"tokens": 1_000_000})
        self.assertEqual(one["iwu"], two["iwu"])
        self.assertEqual(measure([one, two])["resource_totals"]["tokens"], 1_000_001)

    def test_missing_resource_fails_ratio_closed(self):
        rows = [
            record("a", True, resources={"joules": 1}),
            record("b", True, resources={"joules": None}),
        ]
        self.assertIsNone(measure(rows)["iwu_per_resource"]["joules"])

    def test_architecture_neutral_records(self):
        systems = ["llm", "random-forest", "jev", "agent"]
        values = []
        for system in systems:
            row = record(system, True, 0.4, system_id=system)
            values.append(row["iwu"])
            validate_record(row)
        self.assertTrue(all(value == values[0] for value in values))

    def test_duplicate_episode_fails(self):
        row = record("a", True)
        with self.assertRaisesRegex(IWUError, "duplicate"):
            measure([row, row])

    def test_mixed_comparison_identity_fails(self):
        row = record("a", True)
        for field in ("system_id", "registry_id", "verifier_id", "reference_id"):
            changed = record("b", True, **{field: f"{field}:changed"})
            with self.subTest(field=field), self.assertRaisesRegex(IWUError, "mixed"):
                measure([row, changed])

    def test_tampering_is_detected(self):
        row = record("a", True, 0.25)
        mutations = [
            {**row, "accepted": False},
            {**row, "reference_ticks": row["reference_ticks"] + 1},
            {**row, "reference_probability": 0.5},
            {**row, "difficulty_bits": 999},
            {**row, "iwu": 999},
            {**row, "identity_sha256": "0" * 64},
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(IWUError):
                validate_record(mutation)

    def test_empirical_source_tampering_is_detected(self):
        row = observe(
            episode_id="a",
            accepted=True,
            block_id="a",
            reference_successes=3,
            reference_trials=10,
            **COMMON,
        )
        changed_source = {**row["reference_source"], "successes": 4}
        with self.assertRaises(IWUError):
            validate_record({**row, "reference_source": changed_source})
        with self.assertRaises(IWUError):
            validate_record({**row, "reference_source": {**row["reference_source"], "extra": 1}})

    def test_invalid_inputs_fail(self):
        with self.assertRaises(IWUError):
            record("a", 1)  # type: ignore[arg-type]
        with self.assertRaises(IWUError):
            record("a", True, 0)
        with self.assertRaises(IWUError):
            resolve_reference(reference_successes=4, reference_trials=3)
        with self.assertRaises(IWUError):
            record("a", True, resources={"cost_usd": -1})
        with self.assertRaises(IWUError):
            record(" a ", True)

    def test_fixed_s20_resolution(self):
        row = record("a", True)
        self.assertEqual(row["reference_denominator"], 2**20)
        with self.assertRaises(IWUError):
            validate_record({**row, "reference_denominator": 2**16})

    def test_unicode_identity_is_normalized_cross_language(self):
        decomposed = "cafe\u0301"
        row = record(decomposed, True)
        self.assertEqual(row["episode_id"], "caf\u00e9")
        validate_record(row)

    def test_block_bootstrap_scope_is_explicit(self):
        rows = []
        for block in range(12):
            for item in range(5):
                rows.append(
                    record(
                        f"{block}-{item}",
                        (block + item) % 3 != 0,
                        0.5,
                        block_id=str(block),
                    )
                )
        interval = block_bootstrap_interval(rows, iterations=300, seed=42)
        self.assertEqual(interval["scope"], "fixed_reference_candidate_blocks_only")
        self.assertFalse(interval["reference_estimation_uncertainty_included"])
        self.assertTrue(math.isfinite(interval["lower_iwu_per_episode"]))
        self.assertLessEqual(
            interval["lower_iwu_per_episode"], interval["upper_iwu_per_episode"]
        )

    def test_bootstrap_requires_multiple_blocks(self):
        rows = [record("a", True, block_id="same"), record("b", False, block_id="same")]
        with self.assertRaisesRegex(IWUError, "two"):
            block_bootstrap_interval(rows)


if __name__ == "__main__":
    unittest.main()
