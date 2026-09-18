/** Minimal IWU-S20 integration example. */

import { measure, observe } from "../iwu.mjs";

const verifier = (output) => output.resolved === true;
const outputs = [{ resolved: true }, { resolved: false }, { resolved: true }];
const costs = [0.0031, 0.0028, 0.0033];

const records = outputs.map((output, index) => observe({
  episodeId: `request-${index + 1}`,
  systemId: "support-agent-v4@sha256:demo",
  accepted: verifier(output),
  registryId: "support-workload-v1@sha256:demo",
  stratumId: "billing/en/email",
  verifierId: "resolved-v3@sha256:demo",
  referenceId: "production-v1@sha256:demo",
  blockId: `customer-${index + 1}`,
  referenceSuccesses: 73,
  referenceTrials: 100,
  resources: { cost_usd: costs[index], input_tokens: 1400 + (index + 1) * 10 },
}));

console.log(measure(records));
