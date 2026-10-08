"""Geometry and case-selection checks for the independent-river diagnostic."""
from pathlib import Path
import sys
import unittest

import numpy as np
from shapely.geometry import LineString, MultiLineString, Point, GeometryCollection

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bin/analysis'))
from check_abzucht_river_alignment import line_samples, representative


class RiverAlignmentTest(unittest.TestCase):
    def test_total_length_sampling_does_not_overweight_short_fragments(self):
        geometry=GeometryCollection([MultiLineString([
            LineString([(0,0),(10,0)]),LineString([(100,0),(150,0)])]),Point(200,0)])
        samples=line_samples(geometry,30)
        self.assertEqual(len(samples),2)
        self.assertAlmostEqual(samples[0].x,105)
        self.assertAlmostEqual(samples[1].x,135)

    def test_representative_uses_group_median_with_stable_tie(self):
        values=np.array([.6,.7,.8,.9,.1])
        self.assertEqual(representative(np.array([0,1,2,3]),values),1)
        with self.assertRaises(ValueError):representative(np.array([],dtype=int),values)


if __name__=='__main__':unittest.main()
