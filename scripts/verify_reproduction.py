"""Recompute deterministic outputs twice, audit recorded scores, emit golden examples."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def h(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    tracked=[ROOT/"results/PUBLIC-METRICS.json",ROOT/"results/DERIVED-TASK-SUMMARY.json"]
    initial={str(p.relative_to(ROOT)):h(p) for p in tracked}
    for repetition in range(2):
        subprocess.run([sys.executable,str(ROOT/"scripts/analyze_public.py")],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        assert initial=={str(p.relative_to(ROOT)):h(p) for p in tracked},"non-deterministic numerical output"
    sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"scripts"))
    scorer=module("scorer",ROOT/"tests/test_live_scorer.py")
    tasks=json.loads((ROOT/"live/TASKS.json").read_text());key=json.loads((ROOT/"live/SCORING-KEY.json").read_text())
    assert {t["id"]:scorer.independent_answer(t) for t in tasks}==key
    live=json.loads((ROOT/"live/RESULTS.json").read_text())
    answers_checked=0
    for run in live.get("runs",[]):
        cand=(run["final_answer"] or {}).get("answers",{})
        expected=sum(type(cand.get(k)) is int and cand.get(k)==v for k,v in key.items())
        assert expected==run["accepted_count"]
        answers_checked+=len(key)
    testmod=module("test_iwu_examples",ROOT/"tests/test_iwu.py")
    registry,assignments,ledger=testmod.fixture()
    from iwu import calculate
    traces=module("test_trace_examples",ROOT/"tests/test_trace.py")
    trace,blobs=traces.fixture()
    from trace_audit import audit
    audit_result=audit(trace,blobs)
    ex=ROOT/"examples";ex.mkdir(exist_ok=True)
    for name,doc in [("registry",registry),("assignments",assignments),("ledger",ledger),
                     ("expected-score",calculate(registry,assignments,ledger)),("trace",trace),
                     ("artifacts-base64",{k:base64.b64encode(v).decode() for k,v in blobs.items()})]:
        (ex/f"{name}.json").write_text(json.dumps(doc,indent=2)+"\n")
    result=dict(deterministic_reexecutions=2,byte_identical=True,tracked_hashes=initial,
                independent_live_key_checks=len(key),recorded_answers_rescored=answers_checked,
                example_trace_audit=audit_result,external_independent_reviewer=False,
                note="Same local environment; proves deterministic reproduction here, not cross-platform or independent replication.")
    (ROOT/"results/REPRODUCTION.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":main()
