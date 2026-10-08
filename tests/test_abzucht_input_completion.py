"""TOOLING regression checks for explicit applicability and data replacements."""
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'bin/analysis'),str(Path(__file__).resolve().parents[1]/'bin/acquire')]
from complete_abzucht_inputs import strict_criteria,terrain_ls,weighted
from pull_abzucht_soilgrids2017 import depth_average


class InputCompletionTest(unittest.TestCase):
    def test_missing_soil_not_renormalized(self):
        parts={'soil_k_factor':np.array([[np.nan,.4]]),'ls_factor':np.array([[.5,.6]]),'c_factor':np.array([[.7,.8]])}
        result=strict_criteria(parts,{'sediment':{'soil_k_factor':.25,'ls_factor':.5,'c_factor':.25}},np.ones((1,2),bool))['sediment']
        self.assertTrue(np.isnan(result[0,0]));self.assertAlmostEqual(result[0,1],.6,places=6)

    def test_channel_is_explicit_not_applicable(self):
        parts={'soil_k_factor':np.array([[.4,np.nan]]),'ls_factor':np.array([[np.nan,np.nan]]),'c_factor':np.array([[.8,.8]])}
        result=strict_criteria(parts,{'sediment':{'soil_k_factor':.25,'ls_factor':.5,'c_factor':.25}},np.ones((1,2),bool),np.ones((1,2),bool))['sediment']
        self.assertAlmostEqual(result[0,0],.6,places=6)
        self.assertTrue(np.isnan(result[0,1]))
        self.assertTrue(np.isnan(parts['ls_factor']).all())

    def test_ls_formula_zero_slope_and_invalid(self):
        result=terrain_ls(np.array([[0.,np.nan,30.]]),np.array([[100.,100.,1e7]]))
        np.testing.assert_allclose(result,[[0.,np.nan,50.]])

    def test_depth_integration_linear_function(self):
        # Linear profile K(z)=z integrates to 15 over 0–30 cm.
        self.assertEqual(depth_average([0.,5.,15.,30.]),15.)
        with self.assertRaises(ValueError):depth_average([1.,2.])

    def test_weighted_strict_support_and_precision(self):
        result=weighted({'a':np.array([[.6-1e-9,.5]]),'b':np.array([[.6-1e-9,np.nan]])},
                        {'a':.5,'b':.5},np.ones((1,2),bool))
        self.assertTrue(result[0,0]>=.6);self.assertTrue(np.isnan(result[0,1]))


if __name__=='__main__':unittest.main()
