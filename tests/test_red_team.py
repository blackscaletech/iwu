import math
import random
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from iwu import calculate,InvalidLedger
from trace_audit import audit
from uncertainty import bounded_sum_interval
from test_iwu import fixture,rehash
from test_trace import fixture as trace_fixture


class RedTeamTests(unittest.TestCase):
    def test_monotonicity_and_work_bounds(self):
        rng=random.Random(888)
        for k in range(1000):
            with self.subTest(case=k):
                r,a,l=fixture()
                for t in r["tasks"]:t["reference_minutes"]=rng.uniform(.01,10000)
                for e in l["episodes"]:e["outcome"]=rng.choice(["accepted","rejected"])
                rehash(r,a,l);before=calculate(r,a,l)["work_per_assignment"]
                e=rng.choice(l["episodes"]);e["outcome"]="accepted"
                after=calculate(r,a,l)["work_per_assignment"]
                self.assertGreaterEqual(after,before)
                self.assertGreaterEqual(before,0)
                self.assertLessEqual(after,sum(t["probability"]*t["reference_minutes"] for t in r["tasks"]))

    def test_huge_integer_is_controlled_rejection(self):
        r,a,l=fixture();l["episodes"][0]["charges"][0]["amount"]=10**1000
        with self.assertRaises(InvalidLedger):calculate(r,a,l)

    def test_cost_aggregate_overflow_is_controlled_rejection(self):
        r,a,l=fixture();e=l["episodes"][0];e["charges"][0]["amount"]=1e308
        e["charges"].append(dict(charge_id="extra",amount=1e308,currency="USD",category="inference",covers=["extra-event"]))
        with self.assertRaises(InvalidLedger):calculate(r,a,l)

    def test_numeric_model_identity_rejected(self):
        t,b=trace_fixture();t["expected_model"]=t["effective_model"]=7
        with self.assertRaises(InvalidLedger):audit(t,b)

    def test_string_tool_allowlist_rejected(self):
        t,b=trace_fixture();t["allowed_tools"]="calculator"
        with self.assertRaises(InvalidLedger):audit(t,b)

    def test_bounded_interval_formula(self):
        z=bounded_sum_interval(.5,[.01]*100)
        radius=math.sqrt(math.log(40)/200)
        self.assertAlmostEqual(z[0],.5-radius);self.assertAlmostEqual(z[1],.5+radius)

    def test_bounded_interval_at_ceiling_is_not_degenerate(self):
        lo,hi=bounded_sum_interval(1.,[1/48]*48)
        self.assertLess(lo,.99);self.assertEqual(hi,1.)

    def test_correlated_blocks_widen_bound(self):
        independent=bounded_sum_interval(.5,[.01]*100)
        blocks=bounded_sum_interval(.5,[.1]*10)
        self.assertLess(blocks[0],independent[0]);self.assertGreater(blocks[1],independent[1])


if __name__=="__main__":unittest.main()
