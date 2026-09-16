"""Fresh synthetic validation; calibrated interval claims remain assumption-bound."""
import json
import math
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from uncertainty import bounded_sum_interval,lower_confidence_credit


def wilson(k,n):
    # Descriptive Monte Carlo interval for an independently repeated coverage indicator.
    z=1.959963984540054;p=k/n;d=1+z*z/n
    center=(p+z*z/(2*n))/d
    width=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [center-width,center+width]


def main():
    results=[];experiments=2000
    scenarios=["ordinary_independent","concentrated_weights","near_ceiling","near_floor","family_correlated","whole_sample_correlated_negative_control"]
    for si,name in enumerate(scenarios):
        rng=np.random.Generator(np.random.PCG64(20261101+si))
        n=60 if si<2 else 12;reps=4;h=np.ones(n)
        p=np.linspace(.2,.8,n) if si==0 else np.full(n,.99 if si==2 else .01 if si==3 else .5)
        if si==1:h[:3]=100
        truth=float(np.mean(h*p));trial_ranges=np.repeat(h/(n*reps),reps).tolist()
        if si==4:block_ranges=[1/4]*4
        elif si==5:block_ranges=[1.]
        else:block_ranges=trial_ranges
        stats={k:dict(hits=0,widths=[],lowers=[]) for k in ["task_bootstrap","trial_bound","block_bound","trial_lower","block_lower"]}
        for _ in range(experiments):
            if si==4:
                # Four independent family coins, each copied across 3 tasks and 4 trials.
                y=np.repeat(rng.binomial(1,.5,size=4),3)
            elif si==5:y=np.full(n,rng.binomial(1,.5))
            else:y=rng.binomial(reps,p)/reps
            contributions=h*y;estimate=float(contributions.mean())
            idx=rng.integers(0,n,size=(500,n))
            q=np.quantile(contributions[idx].mean(axis=1),[.025,.975],method="linear")
            trial=bounded_sum_interval(estimate,trial_ranges);block=bounded_sum_interval(estimate,block_ranges)
            tl=lower_confidence_credit(estimate,trial_ranges)["lower_credit"]
            bl=lower_confidence_credit(estimate,block_ranges)["lower_credit"]
            for key,(lo,hi) in [("task_bootstrap",q),("trial_bound",trial),("block_bound",block)]:
                stats[key]["hits"]+=int(lo<=truth<=hi);stats[key]["widths"].append(float(hi-lo));stats[key]["lowers"].append(float(lo))
            for key,lo in [("trial_lower",tl),("block_lower",bl)]:
                stats[key]["hits"]+=int(lo<=truth);stats[key]["lowers"].append(lo)
        summarized={}
        for key,s in stats.items():
            rate=s["hits"]/experiments
            summarized[key]=dict(coverage_or_lower_validity=rate,coverage_mc_95ci=wilson(s["hits"],experiments),
                mc_standard_error=math.sqrt(rate*(1-rate)/experiments),mean_lower=float(np.mean(s["lowers"])),
                mean_interval_width=float(np.mean(s["widths"])) if s["widths"] else None,
                guarantee_assumptions_met=key.startswith("block") or (key.startswith("trial") and si<4),
                interpretation="Lower methods report P(lower <= true expected credit); interval methods report P(interval contains true expected credit).")
        results.append(dict(scenario=name,seed=20261101+si,experiments=experiments,tasks=n,trials_per_task=reps,
            independent_blocks=len(block_ranges),true_credit=truth,methods=summarized))
        print(json.dumps(dict(scenario=name,coverage={k:v["coverage_or_lower_validity"] for k,v in summarized.items()})),flush=True)
    sample=lower_confidence_credit(1.,[1/48]*48)
    result=dict(status="synthetic_validation_of_uncertainty_rule",point_estimator_changed=False,
        one_sided_nominal_confidence=.95,two_sided_nominal_confidence=.95,
        scenarios=results,all_success_illustration=sample,
        total_synthetic_experiments=sum(r["experiments"] for r in results),
        limitation="No new real model or human data. Validity depends on correct independent blocks and fixed truthful bounds; unknown dependence may force vacuous intervals.")
    (ROOT/"results/UNCERTAINTY-CORRECTION.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")


if __name__=="__main__":main()
