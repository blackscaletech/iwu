"""IWU v0.1 accounting kernel. Standard library only; not a trace certifier."""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict


class InvalidLedger(ValueError):
    pass


def canonical_hash(value):
    """Restricted JSON: UTF-8, sorted keys, no whitespace, no NaN/Infinity.

    This is a Python reference encoding, NOT a claim of RFC 8785 conformance.
    Interchange users must hash the frozen registry bytes, or agree this encoding.
    """
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise InvalidLedger(message)


def number(value, *, positive=False):
    require(type(value) in (int, float), "finite number required")
    try:
        converted = float(value)
    except (OverflowError, ValueError):
        raise InvalidLedger("number exceeds finite float representation") from None
    require(math.isfinite(converted), "finite number required")
    require(converted > 0 if positive else converted >= 0, "invalid sign")
    return converted


def safe_sum(values):
    try:
        result = math.fsum(values)
    except OverflowError:
        raise InvalidLedger("aggregate exceeds finite float representation") from None
    require(math.isfinite(result), "non-finite aggregate")
    return result


def identifier(value):
    require(isinstance(value, str) and bool(value.strip()), "nonempty identifier required")
    return value


def sha(value):
    require(isinstance(value, str) and len(value) == 64 and
            all(c in "0123456789abcdef" for c in value), "SHA-256 required")


def calculate(registry, assignments, ledger):
    """Task-macro expected work and total-cost accounting with missingness bounds.

    Each assignment is one external task episode. Retries are within an episode.
    Evidence digests and completeness flags are validated structurally only.
    """
    require(registry["unit"] == "IWU-E60", "unknown unit")
    identifier(registry["workload_id"])
    identifier(registry["version"])
    tasks = registry["tasks"]
    require(bool(tasks), "empty workload")
    tids = [identifier(t["task_id"]) for t in tasks]
    require(len(set(tids)) == len(tids), "duplicate task id")
    for t in tasks:
        number(t["probability"], positive=True)
        number(t["reference_minutes"], positive=True)
        require(t["calibration"] in ("measured", "estimated"), "unknown calibration")
    require(math.isclose(math.fsum(t["probability"] for t in tasks), 1,
                         rel_tol=0, abs_tol=1e-12), "probabilities must sum to one")
    rh = canonical_hash(registry)
    require(assignments["workload_hash"] == rh == ledger["workload_hash"],
            "frozen workload hash mismatch")
    require(identifier(assignments["system_id"]) == identifier(ledger["system_id"]),
            "system mismatch")
    identifier(ledger["cost_boundary"])
    identifier(ledger["currency"])
    expected = assignments["episodes"]
    eids = [identifier(e["episode_id"]) for e in expected]
    require(len(set(eids)) == len(eids), "duplicate assignment id")
    emap = {e["episode_id"]: e["task_id"] for e in expected}
    require(set(emap.values()) == set(tids), "every task needs assigned episodes; no extra tasks")
    episodes = ledger["episodes"]
    ids = [identifier(e["episode_id"]) for e in episodes]
    require(len(set(ids)) == len(ids), "duplicate episode id")
    require(set(ids) <= set(eids), "undeclared episode")
    by_id = {e["episode_id"]: e for e in episodes}
    charge_ids, covered_events = set(), set()
    per_task = defaultdict(list)
    missing = []
    for eid, tid in emap.items():
        if eid not in by_id:
            per_task[tid].append((0., 1., 0., False))
            missing.append(eid)
            continue
        e = by_id[eid]
        require(e["task_id"] == tid, "assignment task mismatch")
        require(e["outcome"] in ("accepted", "rejected", "unknown"), "unknown outcome enum")
        require(type(e["cost_complete"]) is bool, "cost completeness must be boolean")
        if e["outcome"] != "unknown":
            sha(e["evidence"]["final_sha256"])
            sha(e["evidence"]["verifier_sha256"])
        charges = []
        for c in e["charges"]:
            cid = identifier(c["charge_id"])
            require(cid not in charge_ids, "duplicate charge id")
            charge_ids.add(cid)
            require(c["currency"] == ledger["currency"], "currency mismatch")
            identifier(c["category"])
            refs = c["covers"]
            require(bool(refs), "charge must identify covered primitive events")
            require(len(set(refs)) == len(refs), "duplicate covered event")
            for ref in refs:
                identifier(ref)
                require(ref not in covered_events, "overlapping charges")
                covered_events.add(ref)
            charges.append(number(c["amount"]))
        outcome = e["outcome"]
        per_task[tid].append((float(outcome == "accepted"),
                             float(outcome != "rejected"),
                             safe_sum(charges), e["cost_complete"]))
    lo_terms, hi_terms, cost_terms, unknown_terms = [], [], [], []
    details = []
    all_cost = True
    for t in tasks:
        values = per_task[t["task_id"]]
        n = len(values)
        p, h = t["probability"], t["reference_minutes"]
        lo = math.fsum(v[0] for v in values) / n
        hi = math.fsum(v[1] for v in values) / n
        # Average before summing to avoid unnecessary overflow from repeated costs.
        cost = safe_sum(v[2] / n for v in values)
        complete = all(v[3] for v in values)
        all_cost &= complete
        lo_terms.append(p*h*lo)
        hi_terms.append(p*h*hi)
        cost_terms.append(p*cost)
        unknown_terms.append(p*(hi-lo))
        details.append(dict(task_id=t["task_id"], assignments=n, acceptance_lower=lo,
                            acceptance_upper=hi, observed_cost_per_assignment=cost,
                            cost_complete=complete))
    lower, upper, cost = math.fsum(lo_terms), math.fsum(hi_terms), math.fsum(cost_terms)
    known = math.fsum(unknown_terms) == 0
    return {
        "unit": "IWU-E60", "workload_hash": rh, "system_id": ledger["system_id"],
        "evidence_level": "accounting-only; calibration and trace authenticity not certified",
        "calibration": "measured-declared" if all(t["calibration"] == "measured" for t in tasks)
                       else "contains-estimated-weights; proxy-only",
        "work_per_assignment": lower if known else None,
        "work_bounds": [lower, upper], "outcome_coverage": 1-math.fsum(unknown_terms),
        "full_cost_per_assignment": cost if all_cost else None,
        "observed_cost_lower_bound": cost, "cost_complete": all_cost,
        "work_per_currency_unit": lower/cost if known and all_cost and cost > 0 else None,
        "missing_episode_ids": missing, "per_task": details,
    }
