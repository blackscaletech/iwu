"""Structural evidence checks for a declared episode, not a trusted monitor."""
import hashlib
from iwu import InvalidLedger, identifier, require, sha


def credit_atoms(reference_minutes, atoms):
    """Fixed fractions of one parent deliverable; internal steps create no credit."""
    import math
    from iwu import number
    number(reference_minutes,positive=True)
    require(bool(atoms),"empty atom set")
    ids=[identifier(a["atom_id"]) for a in atoms]
    require(len(ids)==len(set(ids)),"duplicate deliverable credit")
    for a in atoms:
        number(a["fraction"],positive=True)
        require(type(a["accepted"]) is bool,"binary atomic acceptance required")
    require(math.isclose(math.fsum(a["fraction"] for a in atoms),1,rel_tol=0,abs_tol=1e-12),
            "atomic fractions must conserve parent weight")
    return reference_minutes*math.fsum(a["fraction"] for a in atoms if a["accepted"])


def audit(trace, artifact_bytes):
    """Check explicit trace links and hashes against provided bytes.

    Completeness relative to reality requires external capture/attestation and is
    NOT established by passing this validator. No hidden reasoning is required.
    """
    for k in ("registry_sha256","task_version_sha256","system_config_sha256"):
        sha(trace[k])
    identifier(trace["episode_id"])
    for key in ("expected_model","effective_model","expected_effort","effective_effort"):
        identifier(trace[key])
    require(isinstance(trace["allowed_tools"],list),"tool allowlist must be an array")
    for name in trace["allowed_tools"]:identifier(name)
    require(trace["effective_model"]==trace["expected_model"] and bool(trace["effective_model"]),
            "missing effective model or model drift")
    require(trace["effective_effort"]==trace["expected_effort"] and bool(trace["effective_effort"]),
            "missing effective effort or drift")
    require("chain_of_thought" not in trace and "reasoning_text" not in trace,
            "reasoning text is not part of the interchange")
    for key,value in artifact_bytes.items():
        sha(key);require(hashlib.sha256(value).hexdigest()==key,"artifact content hash mismatch")
    available=set(trace["declared_inputs"])
    require(available<=set(artifact_bytes),"missing declared input artifacts")
    expected=trace["expected_span_ids"]
    require(len(set(expected))==len(expected),"duplicate declared span")
    spans=trace["spans"];ids=[s["span_id"] for s in spans]
    require(len(set(ids))==len(ids) and set(ids)==set(expected),"missing, extra, or duplicate spans")
    require(sum(s["parent_id"] is None for s in spans)==1,"exactly one episode root required")
    require(spans[0]["parent_id"] is None and spans[0]["kind"]=="episode","episode root must be first")
    by_id={s["span_id"]:s for s in spans}
    # Parent IDs and causal predecessor IDs both form a DAG; topological order required.
    seen=set();producers={}
    for s in spans:
        identifier(s["span_id"])
        parent=s["parent_id"]
        require(parent is None or parent in seen,"invalid parent order or cycle")
        require(set(s["predecessor_ids"])<=seen,"invalid predecessor order or cycle")
        require(type(s["start_ns"]) is int and type(s["end_ns"]) is int and
                0<=s["start_ns"]<=s["end_ns"],"invalid timestamps")
        if parent:
            p=by_id[parent]
            require(p["start_ns"]<=s["start_ns"]<=s["end_ns"]<=p["end_ns"],"child outside parent interval")
        require(s["kind"] in ("episode","model","tool","verify"),"unknown span kind")
        if s["kind"] in ("model","tool"):
            require(not (set(s["consumes"]) & set(trace["executor_forbidden_inputs"])),
                    "executor received rubric/solution or other forbidden input")
        if s["kind"]=="tool":require(s["tool_name"] in trace["allowed_tools"],"undeclared tool route")
        if s["kind"]=="model":
            require(s["model"]==trace["expected_model"],"span model drift")
            require(s["effort"]==trace["expected_effort"],"span effort drift")
        require("reasoning_text" not in s and "chain_of_thought" not in s,"reasoning text prohibited")
        require(set(s["consumes"])<=available,"undeclared or future context")
        for a in s["consumes"]:
            if a in producers:
                require(producers[a] in s["predecessor_ids"],"missing declared artifact predecessor")
                require(by_id[producers[a]]["end_ns"]<=s["start_ns"],"future artifact consumption")
        for a in s["produces"]:
            require(a in artifact_bytes,"missing produced artifact content")
            require(a not in producers,"multiple producers for one artifact commitment")
            producers[a]=s["span_id"]
        available.update(s["produces"]);seen.add(s["span_id"])
    require(trace["final_artifact_sha256"] in producers,"missing final artifact producer")
    require(trace["verification_artifact_sha256"] in producers,"missing verification evidence")
    require(by_id[producers[trace["verification_artifact_sha256"]]]["kind"]=="verify",
            "verification artifact must come from declared verifier span")
    return dict(structural_audit="passed",spans=len(spans),artifacts=len(artifact_bytes),
                completeness_attestation="not established by structural audit")
