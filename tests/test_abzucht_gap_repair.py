import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'bin/analysis'))
from repair_abzucht_gaps import census_grid, regularize_flat_twi, score, warp_population, sha, verify_pinned_file


class GapRepairTest(unittest.TestCase):
    def test_same_size_source_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'source'
            path.write_bytes(b'original')
            record = dict(bytes=8,sha256=sha(path))
            verify_pinned_file(path,record)
            path.write_bytes(b'modified')
            with self.assertRaises(ValueError): verify_pinned_file(path,record)

    def test_absent_census_is_not_zero_and_duplicates_fail(self):
        frame = pd.DataFrame(dict(GITTER_ID_100m=['one'], x_mp_100m=[50], y_mp_100m=[50], Einwohner=[3]))
        _, a, _ = census_grid(frame, (0,0,200,100))
        self.assertEqual(a[0,0],3)
        self.assertTrue(np.isnan(a[0,1]))
        with self.assertRaises(ValueError): census_grid(pd.concat([frame,frame]),(0,0,200,100))

    def test_only_flat_missing_positive_sca_is_regularized(self):
        raw = np.array([[5,np.nan,np.nan,np.nan,np.nan]],dtype='float32')
        slope = np.array([[0,0,2,0,0]],dtype='float32')
        sca = np.array([[30,30,30,0,30]],dtype='float32')
        mask = np.array([[True,True,True,True,False]])
        result, changed = regularize_flat_twi(raw,slope,sca,mask,.1)
        np.testing.assert_array_equal(changed,[[False,True,False,False,False]])
        self.assertEqual(result[0,0],5)
        self.assertTrue(np.isnan(result[0,2:]).all())
        self.assertAlmostEqual(result[0,1],np.log(30/np.tan(np.radians(.1))),places=5)

    def test_main_criterion_missing_does_not_get_reweighted(self):
        parts = {'a':np.array([[1,np.nan]],dtype='float32'),'b':np.array([[0,1]],dtype='float32')}
        manifest = dict(component_weights={'first':{'a':1},'second':{'b':1}},main_weights={'first':.4,'second':.6})
        pim,_ = score(parts,manifest,np.ones((1,2),bool))
        self.assertAlmostEqual(pim[0,0],.4)
        self.assertTrue(np.isnan(pim[0,1]))

    def test_population_allocation_conserves_counts_and_zero_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'native.tif'
            with rasterio.open(path,'w',driver='GTiff',count=1,height=1,width=2,dtype='float32',crs='EPSG:3035',transform=from_origin(0,100,100,100),nodata=-200) as d:
                d.write(np.array([[100,0]],dtype='float32'),1)
            ref = dict(height=2,width=4,transform=from_origin(0,100,50,50),crs='EPSG:3035')
            result,check = warp_population(path,ref)
            np.testing.assert_allclose(result,[[25,25,0,0],[25,25,0,0]])
            self.assertLess(check['relative_error'],1e-8)


if __name__ == '__main__': unittest.main()
