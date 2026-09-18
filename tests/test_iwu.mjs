import assert from "node:assert/strict";
import test from "node:test";

import {
  SCALE,
  IWUError,
  blockBootstrapInterval,
  expectedIWU,
  measure,
  observe,
  probabilityToTicks,
  resolveReference,
  scoreFromTicks,
  validateRecord,
} from "../iwu.mjs";

const common = {
  systemId: "system:test:v1",
  registryId: "registry:test:v1",
  stratumId: "stratum:test:v1",
  verifierId: "verifier:test:v1",
  referenceId: "reference:test:v1",
};

function record(episodeId, accepted, probability = 0.5, options = {}) {
  return observe({
    episodeId,
    accepted,
    blockId: options.blockId ?? episodeId,
    referenceProbability: probability,
    ...common,
    ...options,
  });
}

test("unit at even reference", () => {
  assert.equal(record("success", true).iwu, 1);
  assert.equal(record("failure", false).iwu, -1);
});

test("reference expectation is zero", () => {
  for (let ticks = 1; ticks < SCALE; ticks += 997) {
    const p = ticks / SCALE;
    const expectation = p * scoreFromTicks(true, ticks) + (1 - p) * scoreFromTicks(false, ticks);
    assert.ok(Math.abs(expectation) < 1e-12);
  }
});

test("expected sign tracks uplift", () => {
  const ticks = probabilityToTicks(0.3);
  const p = ticks / SCALE;
  assert.ok(expectedIWU(p + 0.1, ticks) > 0);
  assert.equal(expectedIWU(p, ticks), 0);
  assert.ok(expectedIWU(p - 0.1, ticks) < 0);
});

test("reference modes and KT boundaries", () => {
  const ticks = probabilityToTicks(0.25);
  assert.equal(resolveReference({ referenceTicks: ticks }).reference_ticks, ticks);
  assert.equal(resolveReference({ referenceProbability: 0.25 }).reference_ticks, ticks);
  assert.equal(resolveReference({ referenceSuccesses: 0, referenceTrials: 1 }).reference_ticks, ticks);
  assert.ok(resolveReference({ referenceSuccesses: 0, referenceTrials: 128 }).reference_ticks > 0);
  assert.ok(resolveReference({ referenceSuccesses: 128, referenceTrials: 128 }).reference_ticks < SCALE);
});

test("exactly one reference mode is required", () => {
  assert.throws(() => resolveReference(), IWUError);
  assert.throws(() => resolveReference({ referenceTicks: 1, referenceProbability: 0.5 }), IWUError);
  assert.throws(() => resolveReference({ referenceSuccesses: 1 }), IWUError);
});

test("additivity, resources, and strata", () => {
  const rows = [
    record("a", true, 0.25, { stratumId: "hard", resources: { tokens: 10 } }),
    record("b", false, 0.75, { stratumId: "easy", resources: { tokens: 20 } }),
  ];
  const report = measure(rows);
  assert.ok(Math.abs(report.iwu_total - rows.reduce((sum, row) => sum + row.iwu, 0)) < 1e-15);
  assert.equal(report.resource_totals.tokens, 30);
  assert.equal(report.stratum_count, 2);
});

test("missing resources fail ratio closed", () => {
  const rows = [
    record("a", true, 0.5, { resources: { joules: 1 } }),
    record("b", true, 0.5, { resources: { joules: null } }),
  ];
  assert.equal(measure(rows).iwu_per_resource.joules, null);
});

test("duplicates and mixed identities fail", () => {
  const row = record("a", true);
  assert.throws(() => measure([row, row]), IWUError);
  const changed = record("b", true, 0.5, { systemId: "changed" });
  assert.throws(() => measure([row, changed]), IWUError);
});

test("tampering is detected", () => {
  const row = record("a", true, 0.25);
  for (const mutation of [
    { ...row, accepted: false },
    { ...row, reference_ticks: row.reference_ticks + 1 },
    { ...row, reference_probability: 0.5 },
    { ...row, difficulty_bits: 999 },
    { ...row, iwu: 999 },
    { ...row, identity_sha256: "0".repeat(64) },
  ]) {
    assert.throws(() => validateRecord(mutation), IWUError);
  }
  const empirical = observe({
    episodeId: "empirical",
    systemId: "system:test:v1",
    accepted: true,
    registryId: "registry:test:v1",
    stratumId: "stratum:test:v1",
    verifierId: "verifier:test:v1",
    referenceId: "reference:test:v1",
    blockId: "empirical",
    referenceSuccesses: 3,
    referenceTrials: 10,
  });
  assert.throws(
    () => validateRecord({
      ...empirical,
      reference_source: { ...empirical.reference_source, extra: 1 },
    }),
    IWUError,
  );
});

test("invalid inputs fail", () => {
  assert.throws(() => record("a", 1), IWUError);
  assert.throws(() => record("a", true, 0), IWUError);
  assert.throws(() => resolveReference({ referenceSuccesses: 4, referenceTrials: 3 }), IWUError);
  assert.throws(() => record("a", true, 0.5, { resources: { cost_usd: -1 } }), IWUError);
  assert.throws(() => record(" a ", true), IWUError);
});

test("unicode identity is NFC normalized", () => {
  const row = record("cafe\u0301", true);
  assert.equal(row.episode_id, "caf\u00e9");
  validateRecord(row);
});

test("fixed-reference block interval is explicit", () => {
  const rows = [];
  for (let block = 0; block < 12; block += 1) {
    for (let item = 0; item < 5; item += 1) {
      rows.push(record(`${block}-${item}`, (block + item) % 3 !== 0, 0.5, { blockId: `${block}` }));
    }
  }
  const interval = blockBootstrapInterval(rows, { iterations: 300, seed: 42 });
  assert.equal(interval.scope, "fixed_reference_candidate_blocks_only");
  assert.equal(interval.reference_estimation_uncertainty_included, false);
  assert.ok(interval.lower_iwu_per_episode <= interval.upper_iwu_per_episode);
  assert.throws(
    () => blockBootstrapInterval([record("x", true, 0.5, { blockId: "one" })]),
    IWUError,
  );
});
