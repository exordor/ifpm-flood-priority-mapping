"""TOOLING checks for fixed-support proportional weight experiments."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'bin/analysis'))
from tune_abzucht_weights import weights_at, score_at, metrics, best


class WeightSensitivityTest(unittest.TestCase):
    def test_ratio_budget_and_invalid_weights(self):
        base = dict(flood_hazard=.34, sediment=.25, land=.17, env=.1, exposure=.14)
        for f in [.34, .65, .8, 1]:
            w = weights_at(base, f)
            self.assertAlmostEqual(sum(w.values()), 1)
            self.assertAlmostEqual(w['flood_hazard'], f)
            if f < 1:
                self.assertAlmostEqual(w['sediment']/w['exposure'], .25/.14)
        with self.assertRaises(ValueError):
            weights_at(base, 1.1)

    def test_nodata_does_not_become_zero_even_at_endpoint(self):
        a = dict(flood_hazard=np.array([[.8,.4,.7]]), other=np.array([[.2,np.nan,.6]]))
        s = score_at(a, dict(flood_hazard=1.,other=0.), np.array([[True,True,False]]))
        np.testing.assert_allclose(s, [[.8,np.nan,np.nan]])

    def test_uniform_red_expansion_is_not_improvement(self):
        inside=np.array([[True,False]]);ring=~inside
        old=metrics(np.array([[.7,.3]]),inside,ring)
        new=metrics(np.array([[.9,.7]]),inside,ring)
        self.assertGreater(new['inside_mean'],old['inside_mean'])
        self.assertLess(new['high_share_gap'],old['high_share_gap'])

    def test_fixed_threshold_and_empty_support(self):
        s=np.array([[.6,.59,.6,.2]])
        result=metrics(s,np.array([[True,True,False,False]]),np.array([[False,False,True,True]]))
        self.assertEqual(result['inside_high_share'], .5)
        self.assertEqual(result['high_share_gap'], 0)
        with self.assertRaises(ValueError):metrics(s,np.zeros(s.shape,bool),np.ones(s.shape,bool))

    def test_tie_prefers_smaller_weight(self):
        rows=[dict(flood_weight=.8,high_share_gap=.1),dict(flood_weight=.65,high_share_gap=.1)]
        self.assertEqual(best(rows)['flood_weight'], .65)

    def test_threshold_uses_persisted_precision(self):
        a = dict(flood_hazard=np.array([[.6-1e-9,.2]]))
        s = score_at(a,dict(flood_hazard=1.),np.ones((1,2),bool))
        self.assertTrue(np.array_equal(s,s.astype('float32').astype('float64')))
        self.assertEqual(metrics(s,np.array([[True,False]]),np.array([[False,True]]))['inside_high_share'],1.)


if __name__ == '__main__':unittest.main()
