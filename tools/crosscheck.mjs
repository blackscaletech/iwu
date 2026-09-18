/** Deterministic 100,000-record JavaScript cross-language fixture. */

import fs from "node:fs";
import { observe } from "../iwu.mjs";

function lcg(state) {
  return (Math.imul(1664525, state) + 1013904223) >>> 0;
}

function run(count = 100000) {
  let state = 0x5a17c0de;
  let total = 0;
  let minimum = Infinity;
  let maximum = -Infinity;
  let hashXor = 0n;
  for (let index = 0; index < count; index += 1) {
    state = lcg(state);
    const trials = 1 + (state % 10000);
    state = lcg(state);
    const successes = state % (trials + 1);
    state = lcg(state);
    const accepted = Boolean(state & 1);
    const row = observe({
      episodeId: `random-${index}`,
      systemId: "system:crosscheck:v1",
      accepted,
      registryId: "registry:crosscheck:v1",
      stratumId: `counts:${successes}:${trials}`,
      verifierId: "verifier:binary:v1",
      referenceId: "reference:kt:v1",
      blockId: `random-${index}`,
      referenceSuccesses: successes,
      referenceTrials: trials,
    });
    total += row.iwu;
    minimum = Math.min(minimum, row.iwu);
    maximum = Math.max(maximum, row.iwu);
    hashXor ^= BigInt(`0x${row.identity_sha256.slice(0, 16)}`);
  }
  return {
    count,
    identity_hash_prefix_xor_hex: hashXor.toString(16).padStart(16, "0"),
    max_iwu: maximum,
    mean_iwu: total / count,
    min_iwu: minimum,
    total_iwu: total,
  };
}

const actual = run();
const checkIndex = process.argv.indexOf("--check");
if (checkIndex !== -1) {
  const expected = JSON.parse(fs.readFileSync(process.argv[checkIndex + 1], "utf8"));
  if (actual.count !== expected.count) throw new Error("count mismatch");
  if (actual.identity_hash_prefix_xor_hex !== expected.identity_hash_prefix_xor_hex) {
    throw new Error("identity hash mismatch");
  }
  for (const key of ["total_iwu", "mean_iwu", "min_iwu", "max_iwu"]) {
    if (Math.abs(actual[key] - expected[key]) > 1e-11) throw new Error(`${key} mismatch`);
  }
}
console.log(JSON.stringify(actual, null, 2));
