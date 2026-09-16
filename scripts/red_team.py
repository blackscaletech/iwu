"""Supplemental falsification tests. Simulations are not empirical model trials."""
import collections
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"scripts"))
from analyze_public import eligible
from uncertainty import bounded_sum_interval


MUTANTS=[
    ("frozen_workload_check","iwu",'assignments["workload_hash"] == rh == ledger["workload_hash"]','True'),
    ("remove_per_task_averaging","iwu",'lo = math.fsum(v[0] for v in values) / n','lo = math.fsum(v[0] for v in values)'),
    ("duplicate_charge_check","iwu",'cid not in charge_ids','True'),
    ("overlapping_charge_check","iwu",'ref not in covered_events','True'),
    ("ignore_missing_cost","iwu",'all_cost &= complete','all_cost &= True'),
    ("unknown_is_zero","iwu",'float(outcome != "rejected")','float(outcome == "accepted")'),
    ("ignore_all_charges","iwu",'charges.append(number(c["amount"]))','charges.append(0.0)'),
    ("effective_model_drift","trace_audit",'trace["effective_model"]==trace["expected_model"]','True'),
    ("effort_drift","trace_audit",'s["effort"]==trace["expected_effort"]','True'),
    ("future_context","trace_audit",'set(s["consumes"])<=available','True'),
    ("atom_weight_inflation","trace_audit",'math.isclose(math.fsum(a["fraction"] for a in atoms),1,rel_tol=0,abs_tol=1e-12)','True'),
    ("artifact_tamper_check","trace_audit",'hashlib.sha256(value).hexdigest()==key','True'),
]


def mutation_tests():
    child='''import io,json,sys,types,unittest
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root))
args=json.loads(sys.stdin.read());name=args["module"]
m=types.ModuleType(name);m.__file__=str(root/(name+".py"));sys.modules[name]=m
exec(compile(args["source"],m.__file__,"exec"),m.__dict__)
suite=unittest.defaultTestLoader.discover(str(root/"tests"))
r=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
print(json.dumps({"tests":r.testsRun,"failures":len(r.failures),"errors":len(r.errors),"detected":not r.wasSuccessful(),"failing_tests":[str(t) for t,_ in r.failures+r.errors]}))
'''
    results=[]
    for name,mod,old,new in MUTANTS:
        source=(ROOT/f"{mod}.py").read_text();assert source.count(old)==1,(name,source.count(old))
        changed=source.replace(old,new)
        run=subprocess.run([sys.executable,"-c",child,str(ROOT)],input=json.dumps(dict(module=mod,source=changed)),
                            text=True,capture_output=True,timeout=30)
        assert run.returncode==0,f"Mutation runner failed (not a successful kill): {name}: {run.stderr}"
        results.append(dict(mutation=name,**json.loads(run.stdout)))
    return dict(selected_mutants=len(results),detected=sum(r["detected"] for r in results),
                survived=[r["mutation"] for r in results if not r["detected"]],results=results,
                limitation="Hand-selected faults. Not exhaustive mutation coverage or proof of no bugs.")


def simulations():
    results=[]
    for scenario in range(3):
        rng=np.random.Generator(np.random.PCG64(20260930+scenario))
        n=60 if scenario<2 else 12;reps=4
        if scenario==0:
            h=np.ones(n);p=np.linspace(.2,.8,n);name="ordinary_independent"
        elif scenario==1:
            h=np.ones(n);h[:3]=100;p=np.full(n,.5);name="concentrated_reference_weights"
        else:
            h=np.ones(n);p=np.full(n,.99);name="near_ceiling"
        truth=float(np.mean(h*p));samples=1000;resamples=500
        boot_hits=0;bound_hits=0;boot_width=[];bound_width=[];bias=[]
        ranges=np.repeat(h/(n*reps),reps).tolist()
        # These are fixed-registry simulations of independently repeated trials.
        # Task-bootstrap intervals are evaluated deliberately outside their
        # conditional workload-only interpretation to test overbroad claims.
        for _ in range(samples):
            y=rng.binomial(reps,p)/reps;w=h*y;estimate=float(w.mean())
            idx=rng.integers(0,n,size=(resamples,n));b=w[idx].mean(axis=1)
            lo,hi=np.quantile(b,[.025,.975],method="linear")
            blo,bhi=bounded_sum_interval(estimate,ranges)
            boot_hits+=lo<=truth<=hi;bound_hits+=blo<=truth<=bhi
            boot_width.append(hi-lo);bound_width.append(bhi-blo);bias.append(estimate-truth)
        coverage=boot_hits/samples;bc=bound_hits/samples
        results.append(dict(scenario=name,seed=20260930+scenario,experiments=samples,
            tasks=n,trials_per_task=reps,bootstrap_resamples=resamples,true_reference_credit=truth,
            estimator_bias=float(np.mean(bias)),estimator_rmse=float(np.sqrt(np.mean(np.square(bias)))),
            task_bootstrap_empirical_coverage=float(coverage),coverage_monte_carlo_se=float(math.sqrt(coverage*(1-coverage)/samples)),
            task_bootstrap_mean_interval_width=float(np.mean(boot_width)),
            independent_bounded_sum_coverage=float(bc),bounded_sum_mean_interval_width=float(np.mean(bound_width)),
            interpretation="Synthetic fixed-registry truth. Conditional task resampling is not a guaranteed trial-uncertainty interval. Bounds assume independent Bernoulli episodes and exact fixed weights."))
    return results


def provider(alias):
    if alias.startswith("Claude"):return "Anthropic"
    if alias.startswith(("GPT-","gpt-","davinci-","o1","o3","o4")):return "OpenAI"
    if alias.startswith("Gemini"):return "Google"
    if alias.startswith("DeepSeek"):return "DeepSeek"
    return None


def cross_provider():
    raw=(ROOT/"sources/metr_runs.jsonl").read_bytes()
    expected=json.loads((ROOT/"SELECTION-LOCK.json").read_text())["source_sha256"]
    assert hashlib.sha256(raw).hexdigest()==expected
    rr=[json.loads(s) for s in raw.splitlines()];rr=[r for r in rr if eligible(r) and provider(r["alias"])]
    counts=collections.defaultdict(collections.Counter)
    for r in rr:counts[r["alias"]][r["task_id"]]+=1
    aliases=[sorted([a for a in counts if provider(a)==pr],key=lambda a:(-sum(n>=4 for n in counts[a].values()),a))[0]
             for pr in ["Anthropic","OpenAI","Google","DeepSeek"]]
    common=set.intersection(*[{t for t,n in counts[a].items() if n>=4} for a in aliases])
    selected=[r for r in rr if r["alias"] in aliases and r["task_id"] in common]
    by_task=collections.defaultdict(list)
    for r in selected:by_task[r["task_id"]].append(r)
    bad=[t for t,rs in by_task.items() if len({r["human_minutes"] for r in rs})>1]
    tids=sorted(common-set(bad));ys=collections.defaultdict(list)
    for r in selected:
        if r["task_id"] in tids:ys[r["alias"],r["task_id"]].append(r)
    h=np.array([by_task[t][0]["human_minutes"] for t in tids])
    p=np.array([[np.mean([r["score_binarized"] for r in ys[a,t]]) for a in aliases] for t in tids]);w=h[:,None]*p
    rng=np.random.Generator(np.random.PCG64(20261001));idx=rng.integers(0,len(tids),size=(10000,len(tids)))
    b=w[idx].mean(axis=1)
    versions=[{r["task_version"] for r in by_task[t]} for t in tids]
    return dict(status="exploratory_proxy_only",selection_rule="One alias per named provider, maximum >=4-repeat coverage; alphabetical ties",
        tasks=len(tids),records=sum(len(v) for v in ys.values()),excluded_inconsistent_weights=bad,
        mixed_version_tasks=sum(len(v)>1 for v in versions),missing_version_tasks=sum(None in v for v in versions),
        single_nonmissing_version_tasks=sum(len(v)==1 and None not in v for v in versions),
        seed=20261001,resamples=10000,systems=[dict(provider=provider(a),alias=a,
            records=sum(len(ys[a,t]) for t in tids),reference_minute_credit_per_task=float(w[:,j].mean()),
            conditional_task_bootstrap_95ci=[float(x) for x in np.quantile(b[:,j],[.025,.975],method="linear")],
            task_macro_acceptance=float(p[:,j].mean()),scaffolds=sorted({str(r["scaffold"]) for t in tids for r in ys[a,t]}))
            for j,a in enumerate(aliases)],
        claim="Feasible calculation across recorded provider aliases; not measurement invariance, current provider performance or independent replication.")


def counterexamples():
    a=np.array([1.,0.]);b=np.array([0.,1.]);h=np.array([1.,60.])
    scores=[]
    for mix in [[.99,.01],[.5,.5]]:
        aa=float(np.sum(np.array(mix)*h*a));bb=float(np.sum(np.array(mix)*h*b))
        scores.append(dict(mix=mix,A=aa,B=bb,winner="A" if aa>bb else "B"))
    assert scores[0]["winner"]!=scores[1]["winner"]
    # Two p-vectors have equal expected work, different per-task reliability.
    equal=[float(np.mean([1.,0.])),float(np.mean([.5,.5]))]
    assert equal[0]==equal[1]
    return dict(workload_ranking_reversal=scores,equal_work_different_reliability=dict(A=[1.,0.],B=[.5,.5],scores=equal),
        selective_missing=dict(assignments=100,observed_successes=40,missing=60,
            naive_complete_case_acceptance=40/40,identified_acceptance_bounds=[40/100,(40+60)/100]),
        cost_ratio=dict(episode_credit=[1.,1.],episode_cost=[1.,100.],
            ratio_of_means=float(np.mean([1.,1.])/np.mean([1.,100.])),
            erroneous_mean_of_ratios=float(np.mean([1/1,1/100]))),
        common_mode_baseline_error=dict(multiplier=2,score_level_multiplier=2,rankings_changed=False),
        implication="W is not a reliability floor, workload-invariant rank, time-saved estimate or economic value. Stable rankings can coexist with erroneous levels.")


def main():
    result=dict(status="supplemental_post_pilot_red_team",mutation=mutation_tests(),simulations=simulations(),
                cross_provider=cross_provider(),counterexamples=counterexamples())
    (ROOT/"results/RED-TEAM.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"mutation":{k:v for k,v in result['mutation'].items() if k!='results'},
                      "simulations":result['simulations'],"cross_provider":result['cross_provider'],
                      "counterexamples":result['counterexamples']},indent=2))


if __name__=="__main__":main()
