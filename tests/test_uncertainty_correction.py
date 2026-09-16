import math
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from uncertainty import lower_confidence_credit,incomplete_outcome_interval,bounded_sum_interval
from iwu import InvalidLedger


class CorrectedUncertaintyTests(unittest.TestCase):
    def test_one_sided_formula(self):
        r=lower_confidence_credit(.5,[.01]*100)
        self.assertAlmostEqual(r["lower_credit"],.5-math.sqrt(math.log(20)/200))
        self.assertAlmostEqual(r["one_sided_confidence"],.95)
    def test_all_success_is_not_certainty(self):
        r=lower_confidence_credit(1.,[1/48]*48)
        self.assertGreater(r["lower_credit"],0)
        self.assertLess(r["lower_credit"],1)
    def test_one_sided_tighter_than_two_sided_lower(self):
        self.assertGreater(lower_confidence_credit(.5,[.01]*100)["lower_credit"],bounded_sum_interval(.5,[.01]*100)[0])
    def test_independent_repetition_sqrt_scaling(self):
        a=lower_confidence_credit(.5,[.01]*100)["uncertainty_margin"]
        b=lower_confidence_credit(.5,[1/400]*400)["uncertainty_margin"]
        self.assertAlmostEqual(a/2,b)
    def test_complete_dependence_is_vacuous(self):
        r=lower_confidence_credit(1.,[1.])
        self.assertEqual(r["lower_credit"],0)
        self.assertEqual(bounded_sum_interval(1.,[1.]),[0.,1.])
    def test_arbitrary_missing_outcomes_widen_interval(self):
        complete=incomplete_outcome_interval(.4,.4,[.01]*100)
        missing=incomplete_outcome_interval(.4,1.,[.01]*100)
        self.assertEqual(complete[0],missing[0]);self.assertGreater(missing[1],complete[1])
    def test_missing_outcomes_never_increase_lower_credit(self):
        a=lower_confidence_credit(.7,[.01]*100)["lower_credit"]
        b=lower_confidence_credit(.4,[.01]*100)["lower_credit"]
        self.assertLess(b,a)
    def test_invalid_observed_bounds(self):
        with self.assertRaises(InvalidLedger):incomplete_outcome_interval(.8,.2,[.1]*10)
        with self.assertRaises(InvalidLedger):lower_confidence_credit(2.,[1.])
        with self.assertRaises(InvalidLedger):lower_confidence_credit(.5,[1.],alpha=0)


if __name__=="__main__":unittest.main()
