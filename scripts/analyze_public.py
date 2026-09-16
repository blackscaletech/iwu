"""Original, deterministic reanalysis of pinned public outcomes; no upstream code."""
import collections
from decimal import Decimal, localcontext
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from iwu import calculate, canonical_hash

SEED=20260915


def finite(x,positive=False):
    return type(x) in (int,float) and math.isfinite(x) and (x>0 if positive else x>=0)


def eligible(r):
    return (isinstance(r.get("alias"),str) and bool(r["alias"]) and
            isinstance(r.get("task_id"),str) and bool(r["task_id"]) and
            finite(r.get("human_minutes"),positive=True) and
            type(r.get("score_binarized")) in (int,float) and r["score_binarized"] in (0,1))


def ci(x):return [float(v) for v in np.quantile(x,[.025,.975],method="linear")]


def ranks(x):
    return np.array([sum(y<v for y in x)+(sum(y==v for y in x)-1)/2 for v in x],dtype=float)


def rankcorr(a,b):
    ra,rb=ranks(a),ranks(b)
    if np.std(ra)==0 or np.std(rb)==0:return None
    return float(np.corrcoef(ra,rb)[0,1])


def numeric_summary(values):
    values=[float(x) for x in values if finite(x)]
    if not values:return None
    return dict(n=len(values),sum=math.fsum(values),mean=float(np.mean(values)),
                median=float(np.median(values)),minimum=min(values),maximum=max(values))


def main():
    raw=(ROOT/"sources/metr_runs.jsonl").read_bytes()
    provenance=json.loads((ROOT/"sources/PROVENANCE.json").read_text())
    lock=json.loads((ROOT/"SELECTION-LOCK.json").read_text())
    assert hashlib.sha256(raw).hexdigest()==provenance["sha256"]==lock["source_sha256"]
    # The original local protocol is retained as a historical hash commitment.
    # Public methods are a post-analysis account, with their own manifest entry.
    assert lock["protocol_sha256"]=="b047bc26f388355787e13dca6fb81d5f4bbb29c06e96dbff4db338d96e2bc05a"
    rows=[json.loads(s) for s in raw.splitlines()]
    allowed=[r for r in rows if eligible(r) and "human" not in r["alias"].lower()]
    counts=collections.defaultdict(collections.Counter)
    for r in allowed:counts[r["alias"]][r["task_id"]]+=1
    aliases=sorted(counts,key=lambda a:(-sum(v>=4 for v in counts[a].values()),a))[:4]
    assert aliases==lock["aliases"]
    common=set.intersection(*[{t for t,n in counts[a].items() if n>=4} for a in aliases])
    grouped=collections.defaultdict(list)
    for r in allowed:
        if r["alias"] in aliases and r["task_id"] in common:grouped[r["task_id"]].append(r)
    exclusions={}
    for t,rr in grouped.items():
        reasons=[]
        if len({r["human_minutes"] for r in rr})!=1:reasons.append("inconsistent_reference_minutes")
        if len({r["task_family"] for r in rr})!=1:reasons.append("inconsistent_task_family")
        if reasons:exclusions[t]=reasons
    tids=sorted(common-set(exclusions));n=len(tids);m=len(aliases)
    if n<30:raise RuntimeError("Planned selection yields fewer than 30 usable tasks; no substitution")
    selected=[r for t in tids for r in grouped[t]]
    ids=[(r["alias"],r["run_id"]) for r in selected]
    assert len(set(ids))==len(ids),"Duplicate source run IDs: requires investigation"
    h=np.array([grouped[t][0]["human_minutes"] for t in tids],dtype=float)
    families=[grouped[t][0]["task_family"] for t in tids]
    yf=collections.defaultdict(list)
    for r in selected:yf[(r["alias"],r["task_id"])].append(r)
    for rr in yf.values():rr.sort(key=lambda r:str(r["run_id"]))
    ys={(a,t):np.array([r["score_binarized"] for r in yf[a,t]],dtype=float) for a in aliases for t in tids}
    p=np.array([[ys[a,t].mean() for a in aliases] for t in tids])
    work=p*h[:,None];est=work.mean(axis=0)
    rng=np.random.Generator(np.random.PCG64(SEED))
    samples=rng.integers(0,n,size=(10000,n))
    boot=work[samples].mean(axis=1)
    accuracy_boot=p[samples].mean(axis=1)
    weighted_boot=work[samples].sum(axis=1)/h[samples].sum(axis=1)[:,None]
    unique_families=sorted(set(families));fn=len(unique_families)
    fidx=[np.array([i for i,f in enumerate(families) if f==family]) for family in unique_families]
    fsum=np.array([work[idx].sum(axis=0) for idx in fidx])
    fsize=np.array([len(idx) for idx in fidx])
    frng=np.random.Generator(np.random.PCG64(SEED+1))
    fsamples=frng.integers(0,fn,size=(10000,fn))
    family_boot=fsum[fsamples].sum(axis=1)/fsize[fsamples].sum(axis=1)[:,None]

    # Reference-kernel and independently written decimal arithmetic cross-check.
    registry=dict(unit="IWU-E60",workload_id="metr-th10-common170-proxy",
                  version="0.1",tasks=[dict(task_id=t,probability=1/n,reference_minutes=float(h[i]),
                  calibration="estimated" if grouped[t][0]["human_source"]!="baseline" else "measured")
                  for i,t in enumerate(tids)])
    rh=canonical_hash(registry);kernel_checks=[]
    for j,a in enumerate(aliases):
        rr=[r for r in selected if r["alias"]==a]
        assignments=dict(workload_hash=rh,system_id=a,episodes=[dict(episode_id=str(r["run_id"]),task_id=r["task_id"]) for r in rr])
        ledger=dict(workload_hash=rh,system_id=a,currency="USD",cost_boundary="source-generation-cost-only",
                    episodes=[dict(episode_id=str(r["run_id"]),task_id=r["task_id"],
                                   outcome="accepted" if r["score_binarized"]==1 else "rejected",
                                   cost_complete=False,
                                   evidence=dict(final_sha256=hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest(),
                                                 verifier_sha256=provenance["sha256"]),charges=[])
                              for r in rr])
        # Above evidence hashes commit to imported records, NOT original final artifacts/verifiers.
        z=calculate(registry,assignments,ledger)
        with localcontext() as ctx:
            ctx.prec=50
            d=sum((Decimal(str(h[i]))*Decimal(int(ys[a,t].sum()))/Decimal(len(ys[a,t])) for i,t in enumerate(tids)),Decimal(0))/Decimal(n)
        assert math.isclose(z["work_per_assignment"],est[j],rel_tol=1e-12)
        assert math.isclose(float(d),est[j],rel_tol=1e-12)
        assert z["work_per_currency_unit"] is None
        kernel_checks.append(dict(alias=a,numpy=float(est[j]),kernel=z["work_per_assignment"],decimal=float(d),pass_check=True))

    srng=np.random.Generator(np.random.PCG64(SEED+2));half_a=[];half_b=[];cors=[]
    for _ in range(1000):
        pa=np.zeros((n,m));pb=np.zeros((n,m))
        for i,t in enumerate(tids):
            for j,a in enumerate(aliases):
                v=srng.permutation(ys[a,t]);cut=len(v)//2
                pa[i,j]=v[:cut].mean();pb[i,j]=v[cut:].mean()
        wa=(pa*h[:,None]).mean(axis=0);wb=(pb*h[:,None]).mean(axis=0)
        half_a.append(wa);half_b.append(wb);cors.append(rankcorr(wa,wb))
    half_a=np.array(half_a);half_b=np.array(half_b);diff=np.abs(half_a-half_b)
    ranking_disagree=sum(not np.array_equal(ranks(x),ranks(y)) for x,y in zip(half_a,half_b))/1000
    valid_cors=[v for v in cors if v is not None]
    fweights=np.array([1/(fn*len(fidx[unique_families.index(f)])) for f in families])
    family_equal=(work*fweights[:,None]).sum(axis=0)
    long_order=sorted(range(n),key=lambda i:(-h[i],tids[i]))
    nremove=math.ceil(n*.1);longest=long_order[:nremove];keep=long_order[nremove:]
    trimmed=work[keep].mean(axis=0)
    vrng=np.random.Generator(np.random.PCG64(SEED+3));perturb=vrng.uniform(.8,1.2,size=(1000,n))
    perturbed=perturb@work/n
    primary_ranks=ranks(est)
    version_sets=[{r["task_version"] for r in grouped[t]} for t in tids]
    exact=[i for i,v in enumerate(version_sets) if len(v)==1 and None not in v]
    exact_scores=work[exact].mean(axis=0) if exact else None
    bands=[("under_5",h<5),("5_to_under_30",(h>=5)&(h<30)),
           ("30_to_under_120",(h>=30)&(h<120)),("120_plus",h>=120)]
    systems=[]
    for j,a in enumerate(aliases):
        rr=[r for r in selected if r["alias"]==a]
        cost=numeric_summary(r.get("generation_cost") for r in rr)
        tokens=numeric_summary(r.get("tokens_count") for r in rr)
        # Source timestamps are used only when their positive difference is finite.
        deltas=[r["completed_at"]-r["started_at"] for r in rr
                if finite(r.get("completed_at")) and finite(r.get("started_at")) and r["completed_at"]>=r["started_at"]]
        latency=numeric_summary(deltas)
        systems.append(dict(alias=a,records=len(rr),minimum_repeats=min(len(ys[a,t]) for t in tids),
            maximum_repeats=max(len(ys[a,t]) for t in tids),
            reference_minute_credit_per_task=float(est[j]),task_bootstrap_95ci=ci(boot[:,j]),
            family_cluster_bootstrap_95ci=ci(family_boot[:,j]),
            task_macro_acceptance=float(p[:,j].mean()),task_macro_acceptance_95ci=ci(accuracy_boot[:,j]),
            work_weighted_acceptance=float(work[:,j].sum()/h.sum()),work_weighted_acceptance_95ci=ci(weighted_boot[:,j]),
            median_task_reference_credit=float(np.median(work[:,j])),
            split_half_absolute_difference_mean=float(diff[:,j].mean()),
            split_half_absolute_difference_median=float(np.median(diff[:,j])),
            split_half_absolute_difference_95range=ci(diff[:,j]),
            split_half_relative_difference_median=float(np.median(diff[:,j])/est[j]) if est[j]>0 else None,
            longest_10pct_share_of_earned_credit=float(work[longest,j].sum()/work[:,j].sum()) if work[:,j].sum()>0 else None,
            equal_family_score=float(family_equal[j]),drop_longest_10pct_score=float(trimmed[j]),
            perturbed_weight_score_95range=ci(perturbed[:,j]),
            consistent_nonmissing_version_subset_score=float(exact_scores[j]) if exact_scores is not None else None,
            source_generation_cost_proxy=cost,source_tokens=tokens,
            source_timestamp_difference_unverified_units=latency,
            full_episode_cost=None,certified_iwu=None,
            source_fatal_errors=dict(collections.Counter(str(r["fatal_error_from"]) for r in rr)),
            model_metadata=sorted({str(r["model"]) for r in rr}),
            scaffold_metadata=sorted({str(r["scaffold"]) for r in rr}),
            duration_bands={name:dict(tasks=int(mask.sum()),macro_acceptance=float(p[mask,j].mean()),
                reference_minute_credit_per_task=float(work[mask,j].mean())) for name,mask in bands if mask.any()}))
    pairs=[]
    for a,b in itertools.combinations(range(m),2):
        pairs.append(dict(comparison=f"{aliases[b]} minus {aliases[a]}",reference_credit_delta=float(est[b]-est[a]),
                          task_bootstrap_95ci=ci(boot[:,b]-boot[:,a]),family_cluster_bootstrap_95ci=ci(family_boot[:,b]-family_boot[:,a]),
                          macro_acceptance_delta=float((p[:,b]-p[:,a]).mean())))
    results=dict(study_id="iwu-validation-v01",track="retrospective_feasibility",status="proxy_only_not_certified",
        protocol_sha256=lock["protocol_sha256"],source=provenance,python=sys.version.split()[0],numpy=np.__version__,
        selection=dict(source_rows=len(rows),selected_aliases=aliases,common_tasks_before_quality_checks=len(common),
                       included_tasks=n,included_records=len(selected),families=fn,excluded_task_reasons=exclusions,
                       selected_alias_ineligible_rows=sum(r["alias"] in aliases and not eligible(r) for r in rows)),
        calibration=dict(source_human_minutes_mean=float(h.mean()),median=float(np.median(h)),minimum=float(h.min()),maximum=float(h.max()),
            task_sources=dict(collections.Counter(grouped[t][0]["task_source"] for t in tids)),
            human_sources=dict(collections.Counter(grouped[t][0]["human_source"] for t in tids)),
            longest_10pct_tasks=nremove,longest_10pct_share_reference_weight=float(h[longest].sum()/h.sum()),
            effective_reference_weight_task_count=float(h.sum()**2/(h*h).sum()),
            mixed_version_tasks=sum(len(v)>1 for v in version_sets),
            missing_version_tasks=sum(None in v for v in version_sets),consistent_nonmissing_version_tasks=len(exact)),
        uncertainty=dict(resamples=10000,method="paired task percentile; separate family-cluster percentile; NumPy linear quantile",
            seeds=dict(task=SEED,family=SEED+1,split_half=SEED+2,perturbation=SEED+3),
            coverage="Conditional workload-resampling intervals. Exclude human calibration, unseen trials, contamination and judge uncertainty.",
            split_halves=1000,split_half_rank_correlation_median=float(np.median(valid_cors)) if valid_cors else None,
            split_half_rank_correlation_range=[min(valid_cors),max(valid_cors)] if valid_cors else None,
            split_half_full_ranking_disagreement_rate=ranking_disagree),
        sensitivity=dict(equal_family_ranking_changed=not np.array_equal(ranks(family_equal),primary_ranks),
            drop_longest_10pct_ranking_changed=not np.array_equal(ranks(trimmed),primary_ranks),
            independent_uniform_weight_perturbation_20pct_ranking_change_rate=sum(not np.array_equal(ranks(x),primary_ranks) for x in perturbed)/1000,
            note="Changed workloads are distinct estimands; perturbation ranges are not measured calibration CIs."),
        systems=systems,paired_deltas=pairs,arithmetic_crosschecks=kernel_checks,
        certification_failures=["No independently calibrated frozen human reference registry",
            "Task version mixtures and missing version labels", "Harness mixtures; no controlled vendor comparison",
            "Original output/verifier/tool traces not re-audited", "Incomplete full-cost provenance",
            "Retrospective inclusion cannot prove complete assigned-episode capture"],
        claim="Implementable reference-weight accounting; not an intelligence unit, time-saved estimate, endorsed metric, or replicated source study.")
    out=ROOT/"results";out.mkdir(exist_ok=True)
    (out/"PUBLIC-METRICS.json").write_text(json.dumps(results,indent=2,allow_nan=False)+"\n")
    derived=[dict(task_id=t,family=families[i],reference_minutes=float(h[i]),human_source=grouped[t][0]["human_source"],
        task_versions=sorted(str(v) for v in version_sets[i]),
        systems={a:dict(repeats=len(ys[a,t]),accepted=int(ys[a,t].sum()),mean_acceptance=float(p[i,j])) for j,a in enumerate(aliases)})
             for i,t in enumerate(tids)]
    (out/"DERIVED-TASK-SUMMARY.json").write_text(json.dumps(derived,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"selection":results["selection"],"calibration":results["calibration"],
          "scores":[{k:s[k] for k in ["alias","reference_minute_credit_per_task","task_bootstrap_95ci","task_macro_acceptance","split_half_relative_difference_median"]} for s in systems],
          "uncertainty":results["uncertainty"],"sensitivity":results["sensitivity"]},indent=2))


if __name__=="__main__":main()
