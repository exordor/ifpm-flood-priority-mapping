"""Checks for the Goslar comparison helpers in bin/_lib/goslar_comparison.py.

Carried over from test_abzucht_gap_repair, test_abzucht_weight_sensitivity and
test_abzucht_explanation for the functions the full-extent run still uses.
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bin'))
from _lib.goslar_comparison import census_grid, representative, score_at, weights_at


class CensusGridTest(unittest.TestCase):
    def test_absent_census_is_not_zero_and_duplicates_fail(self):
        frame = pd.DataFrame(dict(GITTER_ID_100m=['one'], x_mp_100m=[50], y_mp_100m=[50], Einwohner=[3]))
        _, a, _ = census_grid(frame, (0,0,200,100))
        self.assertEqual(a[0,0],3)
        self.assertTrue(np.isnan(a[0,1]))
        with self.assertRaises(ValueError): census_grid(pd.concat([frame,frame]),(0,0,200,100))


class WeightsTest(unittest.TestCase):
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

    def test_score_uses_persisted_precision(self):
        a = dict(flood_hazard=np.array([[.6-1e-9,.2]]))
        s = score_at(a,dict(flood_hazard=1.),np.ones((1,2),bool))
        self.assertTrue(np.array_equal(s,s.astype('float32').astype('float64')))


class RepresentativeTest(unittest.TestCase):
    def test_median_selection_not_extreme(self):
        a=np.array([[.1,.4,.5,.6,.9]])
        self.assertEqual(representative(np.ones(a.shape,dtype=bool),a),(0,2))

    def test_empty_group_fails_and_masks_hold(self):
        a=np.array([[np.nan,.8,.4]])
        self.assertEqual(representative(np.array([[True,False,True]]),a),(0,2))
        with self.assertRaises(ValueError):representative(np.zeros(a.shape,dtype=bool),a)


if __name__ == '__main__':
    unittest.main()
