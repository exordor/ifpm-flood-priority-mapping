import unittest,sys
from pathlib import Path
import numpy as np
from affine import Affine
from shapely.geometry import Point
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bin/analysis'))
from repair_multiriver_facility_edges import facility_score
class EdgeTests(unittest.TestCase):
 def setUp(self):self.ref={'height':3,'width':3,'transform':Affine(30,0,0,0,-30,90)}
 def test_external_facility_included_without_grid_shift(self):
  points=[Point(75,45),Point(-15,45)]
  old=facility_score(points,self.ref,0);new=facility_score(points,self.ref,68)
  self.assertAlmostEqual(float(old[1,0]),1-60/2000,places=6)
  self.assertAlmostEqual(float(new[1,0]),1-30/2000,places=6)
  self.assertEqual(new[1,2],1)
  self.assertTrue(np.all(new>=old))
 def test_padding_invariant_beyond_decay(self):
  points=[Point(75,45),Point(-15,45),Point(-2200,45)]
  np.testing.assert_array_equal(facility_score(points,self.ref,68),facility_score(points,self.ref,100))
 def test_no_outside_source_preserves_old_values(self):
  np.testing.assert_array_equal(facility_score([Point(75,45)],self.ref,0),facility_score([Point(75,45)],self.ref,68))
 def test_no_points_and_invalid_grid_rejected(self):
  with self.assertRaises(ValueError):facility_score([Point(10000,10000)],self.ref,0)
  with self.assertRaises(ValueError):facility_score([Point(1,1)],dict(self.ref,transform=Affine(30,1,0,0,-30,90)))
if __name__=='__main__':unittest.main()
