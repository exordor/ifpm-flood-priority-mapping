import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bin/analysis'))
from explain_abzucht_comparison import component_support,representative

class ExplanationTest(unittest.TestCase):
    def test_finite_aggregate_does_not_imply_full_support(self):
        arrays=[np.ones((1,2)) for _ in range(14)]
        for i in range(4):arrays[i][0,0]=np.nan
        self.assertEqual(component_support(arrays).tolist(),[[10,14]])
    def test_median_selection_not_extreme(self):
        a=np.array([[.1,.4,.5,.6,.9]])
        self.assertEqual(representative(np.ones(a.shape,dtype=bool),a),(0,2))
    def test_empty_group_fails_and_masks_hold(self):
        a=np.array([[np.nan,.8,.4]])
        self.assertEqual(representative(np.array([[True,False,True]]),a),(0,2))
        with self.assertRaises(ValueError):representative(np.zeros(a.shape,dtype=bool),a)

if __name__=='__main__':unittest.main()
