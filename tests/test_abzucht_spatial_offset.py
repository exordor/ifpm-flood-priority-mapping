"""Meaningful geometry checks for the Abzucht grid-offset diagnostic."""
from pathlib import Path
import sys
import unittest

import numpy as np
from affine import Affine
from shapely.geometry import box

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bin/analysis'))
from diagnose_abzucht_spatial_offset import analyze, classify_distance


class SpatialOffsetTest(unittest.TestCase):
    def test_centre_outside_but_cell_touches_polygon(self):
        # 30 m cells at x=15,45,75,105; HQ100 ends at x=30.
        score=np.full((1,4),.8)
        transform=Affine.translation(0,30)*Affine.scale(30,-30)
        groups,touched,_,rows=analyze(np.zeros(4,dtype=int),np.arange(4),score,
                                      transform,box(0,0,30,30),np.zeros((1,4)))
        np.testing.assert_array_equal(groups,[0,1,2,3])
        np.testing.assert_array_equal(touched,[True,True,False,False])
        self.assertEqual(rows[1]['distance_to_hq100_m'],15.)
        self.assertFalse(rows[1]['inside_hq100_center'])

    def test_buckets_are_exclusive_at_edges(self):
        groups=classify_distance(np.array([0,30,60,90,150,150.001]),
                                 np.array([True,False,False,False,False,False]))
        np.testing.assert_array_equal(groups,[0,1,2,3,4,5])


if __name__=='__main__':
    unittest.main()
