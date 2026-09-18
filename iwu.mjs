/** IWU-S20 zero-dependency JavaScript reference implementation. */

import { createHash } from "node:crypto";

export const SPEC_VERSION = "IWU-S20/0.2-draft";
export const SCALE_BITS = 20;
export const SCALE = 2 ** SCALE_BITS;
const MAX_SAFE_INTEGER = Number.MAX_SAFE_INTEGER;

export class IWUError extends Error {}

function identifier(value, label) {
  if (typeof value !== "string" || value.trim() === "") {
    throw new IWUError(`${label} must be a non-empty string`);
  }
  const normalized = value.normalize("NFC");
  if (normalized !== normalized.trim()) {
    throw new IWUError(`${label} must not have leading or trailing whitespace`);
  }
  return normalized;
}

function numberValue(value, label) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new IWUError(`${label} must be finite`);
  }
  return value;
}

function safeInteger(value, label, minimum = 0) {
  if (!Number.isSafeInteger(value) || value < minimum || value > MAX_SAFE_INTEGER) {
    throw new IWUError(`${label} must be a safe integer of at least ${minimum}`);
  }
  return value;
}

export function probabilityToTicks(referenceProbability) {
  const probability = numberValue(referenceProbability, "referenceProbability");
  if (!(probability > 0 && probability < 1)) {
    throw new IWUError("referenceProbability must be strictly between zero and one");
  }
  const ticks = Math.floor(probability * SCALE + 0.5);
  if (ticks < 1 || ticks >= SCALE) {
    throw new IWUError("referenceProbability is outside the representable S20 range");
  }
  return ticks;
}

export function resolveReference({
  referenceTicks = null,
  referenceProbability = null,
  referenceSuccesses = null,
  referenceTrials = null,
} = {}) {
  const ticksMode = referenceTicks !== null;
  const probabilityMode = referenceProbability !== null;
  const countsMode = referenceSuccesses !== null || referenceTrials !== null;
  if (Number(ticksMode) + Number(probabilityMode) + Number(countsMode) !== 1) {
    throw new IWUError(
      "provide exactly one of referenceTicks, referenceProbability, or the referenceSuccesses/referenceTrials pair",
    );
  }

  let ticks;
  let source;
  if (ticksMode) {
    ticks = safeInteger(referenceTicks, "referenceTicks", 1);
    if (ticks >= SCALE) throw new IWUError(`referenceTicks must be below ${SCALE}`);
    source = { method: "s20_ticks" };
  } else if (probabilityMode) {
    ticks = probabilityToTicks(referenceProbability);
    source = { method: "analytical" };
  } else {
    const successes = safeInteger(referenceSuccesses, "referenceSuccesses", 0);
    const trials = safeInteger(referenceTrials, "referenceTrials", 1);
    if (successes > trials) {
      throw new IWUError("referenceSuccesses must not exceed referenceTrials");
    }
    ticks = probabilityToTicks((successes + 0.5) / (trials + 1));
    source = { method: "krichevsky_trofimov", successes, trials };
  }
  return {
    resolution_bits: SCALE_BITS,
    reference_ticks: ticks,
    reference_denominator: SCALE,
    reference_probability: ticks / SCALE,
    reference_source: source,
  };
}

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, canonicalize(value[key])]),
    );
  }
  return value;
}

export function canonicalJson(value) {
  return JSON.stringify(canonicalize(value));
}

export function sha256Json(value) {
  return createHash("sha256").update(canonicalJson(value), "utf8").digest("hex");
}

export function scoreFromTicks(accepted, referenceTicks) {
  if (typeof accepted !== "boolean") throw new IWUError("accepted must be boolean");
  const ticks = safeInteger(referenceTicks, "referenceTicks", 1);
  if (ticks >= SCALE) throw new IWUError(`referenceTicks must be below ${SCALE}`);
  const probability = ticks / SCALE;
  const difficultyBits = -Math.log2(probability);
  return accepted
    ? difficultyBits
    : -(probability / (1 - probability)) * difficultyBits;
}

export function scoreFromProbability(accepted, referenceProbability) {
  return scoreFromTicks(accepted, probabilityToTicks(referenceProbability));
}

export function expectedIWU(treatmentProbability, referenceTicks) {
  const treatment = numberValue(treatmentProbability, "treatmentProbability");
  if (treatment < 0 || treatment > 1) {
    throw new IWUError("treatmentProbability must be in [0,1]");
  }
  const ticks = safeInteger(referenceTicks, "referenceTicks", 1);
  if (ticks >= SCALE) throw new IWUError(`referenceTicks must be below ${SCALE}`);
  const reference = ticks / SCALE;
  return ((treatment - reference) / (1 - reference)) * -Math.log2(reference);
}

function validatedResources(resources = {}) {
  if (!resources || typeof resources !== "object" || Array.isArray(resources)) {
    throw new IWUError("resources must be an object");
  }
  const output = {};
  for (const rawName of Object.keys(resources)) {
    const name = identifier(rawName, "resource name");
    if (Object.hasOwn(output, name)) {
      throw new IWUError(`duplicate normalized resource name: ${name}`);
    }
    const value = resources[rawName];
    if (value === null) {
      output[name] = null;
    } else {
      const amount = numberValue(value, `resources.${name}`);
      if (amount < 0) throw new IWUError(`resources.${name} must be non-negative`);
      output[name] = amount;
    }
  }
  return Object.fromEntries(Object.entries(output).sort(([left], [right]) => left.localeCompare(right)));
}

function coreIdentity(record) {
  return {
    schema: record.schema,
    episode_id: record.episode_id,
    system_id: record.system_id,
    block_id: record.block_id,
    registry_id: record.registry_id,
    stratum_id: record.stratum_id,
    verifier_id: record.verifier_id,
    reference_id: record.reference_id,
    reference_ticks: record.reference_ticks,
    reference_source: record.reference_source,
    accepted: record.accepted,
  };
}

export function observe({
  episodeId,
  systemId,
  accepted,
  registryId,
  stratumId,
  verifierId,
  referenceId,
  blockId,
  referenceTicks = null,
  referenceProbability = null,
  referenceSuccesses = null,
  referenceTrials = null,
  resources = {},
}) {
  if (typeof accepted !== "boolean") throw new IWUError("accepted must be boolean");
  const reference = resolveReference({
    referenceTicks,
    referenceProbability,
    referenceSuccesses,
    referenceTrials,
  });
  const record = {
    schema: SPEC_VERSION,
    episode_id: identifier(episodeId, "episodeId"),
    system_id: identifier(systemId, "systemId"),
    block_id: identifier(blockId, "blockId"),
    registry_id: identifier(registryId, "registryId"),
    stratum_id: identifier(stratumId, "stratumId"),
    verifier_id: identifier(verifierId, "verifierId"),
    reference_id: identifier(referenceId, "referenceId"),
    reference_ticks: reference.reference_ticks,
    reference_denominator: SCALE,
    reference_source: reference.reference_source,
    accepted,
  };
  record.identity_sha256 = sha256Json(coreIdentity(record));
  record.reference_probability = reference.reference_probability;
  record.difficulty_bits = -Math.log2(reference.reference_probability);
  record.iwu = scoreFromTicks(accepted, reference.reference_ticks);
  record.resources = validatedResources(resources);
  return record;
}

export function validateRecord(input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) {
    throw new IWUError("record must be an object");
  }
  if (input.schema !== SPEC_VERSION) throw new IWUError(`schema must equal ${SPEC_VERSION}`);
  const record = { ...input };
  for (const field of [
    "episode_id",
    "system_id",
    "block_id",
    "registry_id",
    "stratum_id",
    "verifier_id",
    "reference_id",
  ]) {
    const normalized = identifier(record[field], field);
    if (normalized !== record[field]) throw new IWUError(`${field} must use NFC normalization`);
  }
  const ticks = safeInteger(record.reference_ticks, "reference_ticks", 1);
  if (ticks >= SCALE || record.reference_denominator !== SCALE) {
    throw new IWUError("record is not an S20 probability representation");
  }
  if (typeof record.accepted !== "boolean") throw new IWUError("accepted must be boolean");
  const source = record.reference_source;
  if (!source || typeof source !== "object" || Array.isArray(source)) {
    throw new IWUError("reference_source must be an object");
  }
  if (source.method === "krichevsky_trofimov") {
    if (
      Object.keys(source).length !== 3
      || !Object.hasOwn(source, "method")
      || !Object.hasOwn(source, "successes")
      || !Object.hasOwn(source, "trials")
    ) {
      throw new IWUError("unsupported or malformed reference_source");
    }
    const resolved = resolveReference({
      referenceSuccesses: source.successes,
      referenceTrials: source.trials,
    });
    if (resolved.reference_ticks !== ticks) {
      throw new IWUError("reference_source counts do not produce reference_ticks");
    }
  } else if (
    !["analytical", "s20_ticks"].includes(source.method)
    || Object.keys(source).length !== 1
  ) {
    throw new IWUError("unsupported or malformed reference_source");
  }
  const probability = ticks / SCALE;
  if (numberValue(record.reference_probability, "reference_probability") !== probability) {
    throw new IWUError("reference_probability does not match reference_ticks");
  }
  const difficulty = -Math.log2(probability);
  if (Math.abs(numberValue(record.difficulty_bits, "difficulty_bits") - difficulty) > 1e-15) {
    throw new IWUError("difficulty_bits does not match reference_ticks");
  }
  const score = scoreFromTicks(record.accepted, ticks);
  if (Math.abs(numberValue(record.iwu, "iwu") - score) > 1e-12) {
    throw new IWUError("iwu does not match the IWU-S20 formula");
  }
  if (record.identity_sha256 !== sha256Json(coreIdentity(record))) {
    throw new IWUError("identity_sha256 does not match the core record");
  }
  record.resources = validatedResources(record.resources);
  return record;
}

export function measure(inputRecords) {
  if (!Array.isArray(inputRecords) || inputRecords.length === 0) {
    throw new IWUError("at least one record is required");
  }
  const records = inputRecords.map(validateRecord);
  const episodeIds = new Set();
  for (const record of records) {
    if (episodeIds.has(record.episode_id)) {
      throw new IWUError(`duplicate episode_id: ${record.episode_id}`);
    }
    episodeIds.add(record.episode_id);
  }
  for (const field of ["schema", "system_id", "registry_id", "verifier_id", "reference_id"]) {
    if (new Set(records.map((record) => record[field])).size !== 1) {
      throw new IWUError(`mixed ${field} values must not be merged`);
    }
  }
  const total = records.reduce((sum, record) => sum + record.iwu, 0);
  const resourceNames = [...new Set(records.flatMap((record) => Object.keys(record.resources)))].sort();
  const resourceTotals = {};
  const iwuPerResource = {};
  for (const name of resourceNames) {
    const values = records.map((record) => record.resources[name]);
    if (values.some((value) => value === null || value === undefined)) {
      resourceTotals[name] = null;
      iwuPerResource[name] = null;
    } else {
      const amount = values.reduce((sum, value) => sum + numberValue(value, `resources.${name}`), 0);
      resourceTotals[name] = amount;
      iwuPerResource[name] = amount > 0 ? total / amount : null;
    }
  }
  const acceptedCount = records.reduce((sum, record) => sum + Number(record.accepted), 0);
  return {
    schema: SPEC_VERSION,
    system_id: records[0].system_id,
    registry_id: records[0].registry_id,
    verifier_id: records[0].verifier_id,
    reference_id: records[0].reference_id,
    episode_count: records.length,
    block_count: new Set(records.map((record) => record.block_id)).size,
    stratum_count: new Set(records.map((record) => record.stratum_id)).size,
    accepted_count: acceptedCount,
    acceptance_rate: acceptedCount / records.length,
    iwu_total: total,
    iwu_per_episode: total / records.length,
    resource_totals: resourceTotals,
    iwu_per_resource: iwuPerResource,
  };
}

export function blockBootstrapInterval(
  inputRecords,
  { iterations = 2000, confidence = 0.95, seed = 0 } = {},
) {
  const records = inputRecords.map(validateRecord);
  measure(records);
  if (!Number.isInteger(iterations) || iterations < 100) {
    throw new IWUError("iterations must be an integer of at least 100");
  }
  const confidenceValue = numberValue(confidence, "confidence");
  if (!(confidenceValue > 0 && confidenceValue < 1)) {
    throw new IWUError("confidence must be strictly between zero and one");
  }
  const grouped = new Map();
  for (const record of records) {
    if (!grouped.has(record.block_id)) grouped.set(record.block_id, []);
    grouped.get(record.block_id).push(record.iwu);
  }
  const blocks = [...grouped.values()];
  if (blocks.length < 2) {
    throw new IWUError("at least two declared independent blocks are required");
  }
  let state = seed >>> 0;
  const randomIndex = () => {
    state = (Math.imul(1664525, state) + 1013904223) >>> 0;
    return state % blocks.length;
  };
  const estimates = [];
  for (let iteration = 0; iteration < iterations; iteration += 1) {
    let sum = 0;
    let count = 0;
    for (let index = 0; index < blocks.length; index += 1) {
      const block = blocks[randomIndex()];
      sum += block.reduce((left, right) => left + right, 0);
      count += block.length;
    }
    estimates.push(sum / count);
  }
  estimates.sort((left, right) => left - right);
  const quantile = (probability) => {
    const position = probability * (estimates.length - 1);
    const lower = Math.floor(position);
    const upper = Math.ceil(position);
    if (lower === upper) return estimates[lower];
    const fraction = position - lower;
    return estimates[lower] * (1 - fraction) + estimates[upper] * fraction;
  };
  const alpha = (1 - confidenceValue) / 2;
  return {
    scope: "fixed_reference_candidate_blocks_only",
    confidence: confidenceValue,
    iterations,
    block_count: blocks.length,
    point_iwu_per_episode: records.reduce((sum, record) => sum + record.iwu, 0) / records.length,
    lower_iwu_per_episode: quantile(alpha),
    upper_iwu_per_episode: quantile(1 - alpha),
    reference_estimation_uncertainty_included: false,
  };
}
