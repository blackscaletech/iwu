"""Six serial fresh CLI trials; persist final answers/usage, never reasoning events."""
import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import selectors
import shutil
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
MODEL="gpt-5.6-sol"
EFFORT="medium"


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def generate():
    rng=random.Random(20260915);tasks=[];answers={}
    for k in range(4):
        a,b,c,d,e,f=[rng.randint(11,99) for _ in range(6)]
        expr=f"(({a} * {b} - {c}) * {d} + {e} * {f})"
        tid=f"arithmetic-{k+1}";ans=(a*b-c)*d+e*f
        tasks.append(dict(id=tid,family="arithmetic",question=f"Compute the integer value of {expr}."))
        answers[tid]=ans
    for k in range(4):
        n=8;edges=[]
        for i in range(n):
            for j in range(i+1,n):
                if j==i+1 or rng.random()<.55:edges.append([i,j,rng.randint(1,35)])
        dist=[0]+[10**9]*(n-1)
        for i,j,w in edges:dist[j]=min(dist[j],dist[i]+w)
        tid=f"path-{k+1}"
        tasks.append(dict(id=tid,family="shortest_path",question=(
            f"Directed graph nodes 0..7, edges [from,to,positive weight]: {json.dumps(edges)}. "
            "Return only the minimum total path weight from node 0 to node 7, not the path.")))
        answers[tid]=dist[-1]
    for k in range(4):
        items=[[i,rng.randint(1,9),rng.randint(2,35)] for i in range(12)]
        capacity=22;best=-1
        for size in range(4,7):
            for combo in itertools.combinations(items,size):
                if sum(t[1] for t in combo)<=capacity and sum(t[0]%2==0 for t in combo)>=2:
                    best=max(best,sum(t[2] for t in combo))
        tid=f"subset-{k+1}"
        tasks.append(dict(id=tid,family="subset",question=(
            f"Items [id,weight,value]: {json.dumps(items)}. Choose 4, 5 or 6 distinct items, "
            "total weight at most 22, including at least 2 even-numbered item IDs. "
            "Return the largest achievable total value, not the selected subset.")))
        answers[tid]=best
    return tasks,answers


def sanitize_event(event, collected):
    typ=event.get("type","")
    if typ=="turn.completed":collected["usage"]=event.get("usage")
    if typ in ("error","turn.failed"):
        # Error status only; raw transport/authentication diagnostics are not durable study data.
        collected["errors"].append(typ)
    item=event.get("item",{})
    it=item.get("type","")
    if typ=="item.completed" and it=="agent_message":
        collected["messages"].append(item.get("text",""))
    if it in ("command_execution","mcp_tool_call","web_search","file_change") and typ=="item.completed":
        entry={"type":it,"status":item.get("status"),"exit_code":item.get("exit_code")}
        # Persist only event metadata and a command commitment, not arbitrary stdout.
        if "command" in item:entry["command_sha256"]=hashlib.sha256(item["command"].encode()).hexdigest()
        collected["tool_events"].append(entry)
    if event.get("model"):
        collected["reported_models"].append(event["model"])


def invoke(cli, prompt, schema, arm, cap):
    tmp=Path(tempfile.mkdtemp(prefix="iwu-trial-"))
    collected=dict(messages=[],usage=None,tool_events=[],errors=[],reported_models=[])
    proc=None
    try:
        (tmp/"output-schema.json").write_text(json.dumps(schema))
        command=[cli,"exec","--ignore-user-config","--ephemeral","--skip-git-repo-check",
                 "--json","--output-schema",str(tmp/"output-schema.json"),
                 "-m",MODEL,"-c",f'model_reasoning_effort="{EFFORT}"',
                 "-c","mcp_servers={}","-c",'web_search="disabled"',
                 "-c","features.apps=false","-c","features.plugins=false",
                 "-c","features.multi_agent=false","-c","features.js_repl=false",
                 "-c","features.computer_use=false","-s","read-only","-"]
        start=time.monotonic()
        proc=subprocess.Popen(command,cwd=tmp,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL,text=False,start_new_session=True)
        proc.stdin.write(prompt.encode());proc.stdin.close()
        selector=selectors.DefaultSelector();selector.register(proc.stdout,selectors.EVENT_READ)
        buffer=b"";timeout=False
        while selector.get_map():
            if time.monotonic()-start>cap:
                timeout=True;os.killpg(proc.pid,15);break
            for key,_ in selector.select(timeout=.2):
                part=os.read(key.fileobj.fileno(),65536)
                if not part:selector.unregister(key.fileobj);continue
                buffer+=part
                while b"\n" in buffer:
                    line,buffer=buffer.split(b"\n",1)
                    try:sanitize_event(json.loads(line),collected)
                    except (ValueError,TypeError,KeyError):pass
        try:proc.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(proc.pid,9);proc.wait()
        elapsed=time.monotonic()-start
        if buffer:
            try:sanitize_event(json.loads(buffer),collected)
            except (ValueError,TypeError,KeyError):pass
        final=collected["messages"][-1] if collected["messages"] else ""
        result=None
        try:result=json.loads(final)
        except ValueError:pass
        violation=[]
        if timeout:violation.append("wall_clock_cap_exceeded")
        if proc.returncode!=0:violation.append(f"process_exit_{proc.returncode}")
        if result is None:violation.append("missing_or_malformed_final_json")
        if collected["errors"]:violation.append("reported_execution_error")
        if arm=="direct" and collected["tool_events"]:violation.append("direct_arm_used_tools")
        if any(e["type"] in ("mcp_tool_call","web_search","file_change") for e in collected["tool_events"]):
            violation.append("disallowed_tool_type")
        if any(m!=MODEL for m in collected["reported_models"]):violation.append("model_drift")
        return dict(requested_model=MODEL,requested_effort=EFFORT,
                    model_attestation="reported" if collected["reported_models"] else "requested-only; effective model not exposed",
                    reported_models=collected["reported_models"],elapsed_seconds=elapsed,
                    return_code=proc.returncode,timeout=timeout,final_answer=result,
                    final_sha256=hashlib.sha256(final.encode()).hexdigest(),
                    usage=collected["usage"],tool_events=collected["tool_events"],
                    invalid_reasons=violation,dollar_cost=None,
                    cost_note="Existing subscription authentication; no per-episode bill was available.")
    finally:
        if proc is not None and proc.poll() is None:
            os.killpg(proc.pid,9);proc.wait()
        shutil.rmtree(tmp)


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--cli",default="codex")
    args=parser.parse_args()
    out=ROOT/"live";out.mkdir(exist_ok=True)
    if (out/"RESULTS.json").exists():raise SystemExit("Live results already exist; no silent reruns.")
    tasks,answers=generate()
    schema={"type":"object","properties":{"answers":{"type":"object","properties":{
        t["id"]:{"type":"integer"} for t in tasks},"required":[t["id"] for t in tasks],"additionalProperties":False}},
        "required":["answers"],"additionalProperties":False}
    (out/"TASKS.json").write_text(json.dumps(tasks,indent=2)+"\n")
    (out/"SCORING-KEY.json").write_text(json.dumps(answers,indent=2)+"\n")
    (out/"SCHEMA.json").write_text(json.dumps(schema,indent=2)+"\n")
    common=("This is an isolated benchmark, not a repository task. Do not inspect files, configuration, "
        "credentials or previous sessions. Do not use network, MCP, browser, external agents, or memory. "
        "Solve the supplied tasks. Return only the final JSON object with integer answers; do not output explanations "
        "or reasoning. Do not change the model or its reasoning settings. ")
    probe_schema={"type":"object","properties":{"ready":{"type":"boolean"}},"required":["ready"],"additionalProperties":False}
    probe=invoke(args.cli,common+'Do not use any tools. Return {"ready":true}.',probe_schema,"direct",90)
    (out/"PROBE.json").write_text(json.dumps(probe,indent=2)+"\n")
    if probe["invalid_reasons"]:
        summary=dict(status="blocked_before_scored_trials",blocker=probe["invalid_reasons"],runs=[],
                     note="No model fallback. Public-data and accounting tracks remain separate.")
        (out/"RESULTS.json").write_text(json.dumps(summary,indent=2)+"\n")
        print(json.dumps(summary),flush=True);return
    runs=[]
    for rep in range(1,4):
        for arm in ("direct","local_computation"):
            policy=("Do not call any tools. Compute answers directly. " if arm=="direct" else
                "You may use local shell execution ONLY to calculate from the supplied data, such as an inline Python program. "
                "Do not read or write any files, invoke other models, inspect the environment, or access any network. ")
            prompt=common+policy+"Tasks:\n"+json.dumps(tasks)+"\nRequired final schema:\n"+json.dumps(schema)
            print(f"Starting {arm} replicate {rep}",flush=True)
            r=invoke(args.cli,prompt,schema,arm,180)
            r.update(arm=arm,replicate=rep,task_hash=digest(tasks),prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest())
            candidate=(r["final_answer"] or {}).get("answers",{})
            if set(candidate)!=set(answers) or any(type(x) is not int for x in candidate.values()):
                r["invalid_reasons"].append("final_schema_mismatch")
            r["scored_answers"]={k:dict(correct_answer=v,candidate_answer=candidate.get(k),
                                         accepted=type(candidate.get(k)) is int and candidate.get(k)==v)
                                 for k,v in answers.items()}
            r["accepted_count"]=sum(t["accepted"] for t in r["scored_answers"].values())
            r["eligible_for_arm_comparison"]=not r["invalid_reasons"]
            runs.append(r)
            (out/f"{arm}-{rep}.json").write_text(json.dumps(r,indent=2)+"\n")
            print(json.dumps({k:r[k] for k in ["arm","replicate","accepted_count","elapsed_seconds","invalid_reasons","usage"]}),flush=True)
            if "model_drift" in r["invalid_reasons"]:break
        if runs and "model_drift" in runs[-1]["invalid_reasons"]:break
    summary=dict(status="completed",requested_model=MODEL,requested_effort=EFFORT,
                 tasks=12,runs=runs,human_reference_weights=None,iwu_score=None,
                 limitation="Uncalibrated deterministic smoke tasks; no certified IWU, dollar efficiency or causal model ranking.")
    (out/"RESULTS.json").write_text(json.dumps(summary,indent=2)+"\n")


if __name__=="__main__":main()
