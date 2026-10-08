"""Focused boundary and missing-data regression checks for local comparison."""
import sys
from pathlib import Path
import unittest
import numpy as np
from affine import Affine
from shapely.geometry import box, GeometryCollection
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bin/analysis'))
from compare_goslar_multiriver import union_polygons, raster_mask, clean_ring, stats

class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.ref={'width':3,'height':3,'transform':Affine(30,0,0,0,-30,90)}
    def test_union_deduplicates(self):
        self.assertEqual(union_polygons([box(0,0,60,60)]*2).area,3600)
    def test_empty_and_outside(self):
        for g in [GeometryCollection(),box(100,100,120,120)]:
            for touched in [False,True]:self.assertFalse(raster_mask(g,self.ref,touched).any())
    def test_edge_intersection(self):
        g=box(29,31,31,59)
        self.assertEqual(raster_mask(g,self.ref).sum(),0)
        self.assertEqual(raster_mask(g,self.ref,True).sum(),2)
    def test_ring_excludes_other_floods(self):
        target=box(30,30,60,60);other=box(60,0,90,90)
        ring=clean_ring(target,30,union_polygons([target,other]))
        self.assertEqual(ring.intersection(other).area,0)
        self.assertEqual(ring.intersection(target).area,0)
    def test_nodata_not_low_score(self):
        a=np.array([[np.nan,.6,.2]])
        s=stats(a,np.ones(a.shape,bool))
        self.assertEqual(s['valid_cells'],2)
        self.assertEqual(s['high_share'],.5)
        self.assertAlmostEqual(s['mean'],.4)
        empty=stats(a,np.zeros(a.shape,bool))
        self.assertIsNone(empty['mean']);self.assertIsNone(empty['high_share'])

if __name__=='__main__':unittest.main()
