import copy
import json
import math
import random
import sys
import unittest
from decimal import Decimal, localcontext
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from iwu import calculate, canonical_hash, InvalidLedger


def fixture():
    r = dict(unit="IWU-E60", workload_id="demo", version="1", tasks=[
        dict(task_id="a", probability=.5, reference_minutes=2., calibration="measured"),
        dict(task_id="b", probability=.5, reference_minutes=10., calibration="measured")])
    h = canonical_hash(r)
    a = dict(workload_hash=h, system_id="s", episodes=[
        dict(episode_id=str(i), task_id=t) for i,t in enumerate(["a","a","b","b"])])
    l = dict(workload_hash=h, system_id="s", currency="USD", cost_boundary="all-episode-v1",
             episodes=[dict(episode_id=str(i), task_id=t, outcome=y,
                 cost_complete=True, evidence=dict(final_sha256="a"*64, verifier_sha256="b"*64),
                 charges=[dict(charge_id=f"c{i}", amount=1., currency="USD",
                               category="inference", covers=[f"event{i}"])])
                       for i,(t,y) in enumerate(zip(["a","a","b","b"],
                           ["accepted","rejected","accepted","accepted"]))])
    return r,a,l


def rehash(r,a,l):
    a["workload_hash"] = l["workload_hash"] = canonical_hash(r)


def independent_decimal(r,a,l):
    # A separately written implementation for COMPLETE fixtures, no production helpers.
    with localcontext() as ctx:
        ctx.prec = 50
        numerator = Decimal(0)
        denominator = Decimal(0)
        for task in r["tasks"]:
            events = [e for e in l["episodes"] if e["task_id"] == task["task_id"]]
            p = Decimal(str(task["probability"]))
            minutes = Decimal(str(task["reference_minutes"]))
            successes = sum(e["outcome"] == "accepted" for e in events)
            numerator += p*minutes*Decimal(successes)/Decimal(len(events))
            charges = sum((Decimal(str(c["amount"])) for e in events for c in e["charges"]), Decimal(0))
            denominator += p*charges/Decimal(len(events))
        return float(numerator), float(denominator)


class AccountingTests(unittest.TestCase):
    def test_hand_calculated_example(self):
        z=calculate(*fixture())
        self.assertEqual(z["work_per_assignment"],5.5)
        self.assertEqual(z["full_cost_per_assignment"],1.)
        self.assertEqual(z["work_per_currency_unit"],5.5)

    def test_permutation(self):
        r,a,l=fixture(); x=calculate(r,a,l)
        l["episodes"].reverse(); a["episodes"].reverse()
        self.assertEqual(x["work_per_assignment"],calculate(r,a,l)["work_per_assignment"])

    def test_replication(self):
        r,a,l=fixture(); x=calculate(r,a,l)
        for e in copy.deepcopy(l["episodes"]):
            e["episode_id"] += "x"
            for c in e["charges"]:
                c["charge_id"]+="x"; c["covers"]=[x+"x" for x in c["covers"]]
            l["episodes"].append(e)
            a["episodes"].append(dict(episode_id=e["episode_id"],task_id=e["task_id"]))
        z=calculate(r,a,l)
        self.assertEqual(x["work_per_assignment"],z["work_per_assignment"])
        self.assertEqual(x["full_cost_per_assignment"],z["full_cost_per_assignment"])

    def test_conservative_credit_partition(self):
        # Re-express a deliverable in two fixed atoms with equal acceptance and conserved weight.
        r,a,l=fixture(); x=calculate(r,a,l)["work_per_assignment"]
        rr=copy.deepcopy(r); rr["tasks"]=[]; aa=copy.deepcopy(a); aa["episodes"]=[]
        ll=copy.deepcopy(l); ll["episodes"]=[]
        for suffix in ("x","y"):
            for t in r["tasks"]:
                u=copy.deepcopy(t); u["task_id"]+=suffix; u["probability"]*=.5; rr["tasks"].append(u)
            for e in l["episodes"]:
                u=copy.deepcopy(e);u["episode_id"]+=suffix;u["task_id"]+=suffix
                for c in u["charges"]:
                    c["charge_id"]+=suffix;c["covers"]=[v+suffix for v in c["covers"]]
                ll["episodes"].append(u);aa["episodes"].append(dict(episode_id=u["episode_id"],task_id=u["task_id"]))
        rehash(rr,aa,ll)
        self.assertEqual(x,calculate(rr,aa,ll)["work_per_assignment"])

    def test_failed_retry_costs(self):
        r,a,l=fixture(); x=calculate(r,a,l)
        l["episodes"][0]["charges"].append(dict(charge_id="retry",amount=8.,currency="USD",category="inference",covers=["retry-event"]))
        z=calculate(r,a,l)
        self.assertEqual(x["work_per_assignment"],z["work_per_assignment"])
        self.assertEqual(z["full_cost_per_assignment"],3.)
        self.assertLess(z["work_per_currency_unit"],x["work_per_currency_unit"])

    def test_duplicate_episode(self):
        r,a,l=fixture();l["episodes"].append(l["episodes"][0])
        with self.assertRaises(InvalidLedger):calculate(r,a,l)

    def test_duplicate_assignment(self):
        r,a,l=fixture();a["episodes"].append(a["episodes"][0])
        with self.assertRaises(InvalidLedger):calculate(r,a,l)

    def test_undeclared_episode(self):
        r,a,l=fixture();l["episodes"][0]["episode_id"]="unexpected"
        with self.assertRaises(InvalidLedger):calculate(r,a,l)

    def test_duplicate_charge(self):
        r,a,l=fixture();l["episodes"][1]["charges"][0]["charge_id"]="c0"
        with self.assertRaises(InvalidLedger):calculate(r,a,l)

    def test_overlapping_parent_child_charges(self):
        r,a,l=fixture();l["episodes"][1]["charges"][0]["covers"]=["event0"]
        with self.assertRaises(InvalidLedger):calculate(r,a,l)

    def test_missing_record_unknown_not_zero(self):
        r,a,l=fixture();l["episodes"].pop()
        z=calculate(r,a,l)
        self.assertIsNone(z["work_per_assignment"])
        self.assertEqual(z["work_bounds"],[3.,5.5])
        self.assertEqual(z["outcome_coverage"],.75)
        self.assertIsNone(z["full_cost_per_assignment"])

    def test_unknown_outcome(self):
        r,a,l=fixture();l["episodes"][3]["outcome"]="unknown"
        z=calculate(r,a,l);self.assertEqual(z["work_bounds"],[3.,5.5])
        self.assertIsNone(z["work_per_currency_unit"])

    def test_incomplete_cost(self):
        r,a,l=fixture();l["episodes"][0]["cost_complete"]=False
        z=calculate(r,a,l);self.assertEqual(z["work_per_assignment"],5.5)
        self.assertIsNone(z["full_cost_per_assignment"])
        self.assertIsNone(z["work_per_currency_unit"])

    def test_zero_cost_is_not_infinite_efficiency(self):
        r,a,l=fixture()
        for e in l["episodes"]:e["charges"]=[]
        z=calculate(r,a,l);self.assertEqual(z["full_cost_per_assignment"],0)
        self.assertIsNone(z["work_per_currency_unit"])

    def test_invalid_numbers(self):
        for value in [True,False,-1.,float("nan"),float("inf"),"1"]:
            with self.subTest(value=value):
                r,a,l=fixture();l["episodes"][0]["charges"][0]["amount"]=value
                with self.assertRaises(InvalidLedger):calculate(r,a,l)

    def test_probability_sum(self):
        r,a,l=fixture();r["tasks"][0]["probability"]=.6;rehash(r,a,l)
        with self.assertRaises(InvalidLedger):calculate(r,a,l)

    def test_changed_registry_hash(self):
        r,a,l=fixture();r["tasks"][0]["reference_minutes"]*=2
        with self.assertRaises(InvalidLedger):calculate(r,a,l)

    def test_task_mapping_drift(self):
        r,a,l=fixture();l["episodes"][0]["task_id"]="b"
        with self.assertRaises(InvalidLedger):calculate(r,a,l)

    def test_system_drift(self):
        r,a,l=fixture();l["system_id"]="other"
        with self.assertRaises(InvalidLedger):calculate(r,a,l)

    def test_missing_verification(self):
        r,a,l=fixture();l["episodes"][0]["evidence"]["verifier_sha256"]="bad"
        with self.assertRaises(InvalidLedger):calculate(r,a,l)

    def test_currency_mismatch(self):
        r,a,l=fixture();l["episodes"][0]["charges"][0]["currency"]="EUR"
        with self.assertRaises(InvalidLedger):calculate(r,a,l)

    def test_no_credit_for_trace_verbosity(self):
        r,a,l=fixture();x=calculate(r,a,l)
        for e in l["episodes"]:e["tokens"]=1000000;e["tool_event_count"]=999
        self.assertEqual(x,calculate(r,a,l))

    def test_estimated_calibration_disclosure(self):
        r,a,l=fixture();r["tasks"][0]["calibration"]="estimated";rehash(r,a,l)
        self.assertIn("proxy",calculate(r,a,l)["calibration"])

    def test_randomized_crossimplementation_and_scaling(self):
        rng=random.Random(20260915)
        for k in range(1000):
            with self.subTest(case=k):
                r,a,l=fixture()
                for t in r["tasks"]:t["reference_minutes"]=rng.uniform(.01,1000)
                for e in l["episodes"]:
                    e["outcome"]=rng.choice(["accepted","rejected"])
                    e["charges"][0]["amount"]=rng.uniform(.001,100)
                rehash(r,a,l);z=calculate(r,a,l);w,c=independent_decimal(r,a,l)
                self.assertTrue(math.isclose(w,z["work_per_assignment"],rel_tol=1e-12,abs_tol=1e-12))
                self.assertTrue(math.isclose(c,z["full_cost_per_assignment"],rel_tol=1e-12,abs_tol=1e-12))
                scale=rng.uniform(.01,20)
                for t in r["tasks"]:t["reference_minutes"]*=scale
                rehash(r,a,l)
                self.assertTrue(math.isclose(calculate(r,a,l)["work_per_assignment"],w*scale,rel_tol=1e-12,abs_tol=1e-12))


if __name__=="__main__":unittest.main()
