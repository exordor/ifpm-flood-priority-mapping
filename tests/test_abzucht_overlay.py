import importlib.util
import tempfile
import unittest
from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_origin

PATH = Path(__file__).resolve().parents[1] / 'bin/analysis/compare_abzucht_hq100.py'
spec = importlib.util.spec_from_file_location('abzucht', PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class OverlayTest(unittest.TestCase):
    def test_nodata_excluded_and_threshold_edges(self):
        a = np.array([[np.nan, 0, .2, .4, .6, .8, 1.]])
        s = mod.summarize(a, np.ones_like(a, dtype=bool))
        self.assertEqual(s['valid_cells'], 6)
        self.assertEqual(s['class_counts'], [1, 1, 1, 1, 2])
        self.assertEqual(s['high_share'], .5)
        self.assertIsNone(mod.summarize(a, np.zeros_like(a, dtype=bool))['mean'])

    def test_internal_mask_and_grid_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/'masked.tif'
            profile = dict(driver='GTiff',height=2,width=2,count=1,dtype='float32',crs='EPSG:32632',transform=from_origin(0,60,30,30))
            with rasterio.open(p,'w',**profile) as ds:
                ds.write(np.ones((2,2), dtype='float32'),1)
                ds.write_mask(np.array([[0,255],[255,255]],dtype='uint8'))
            a, ref = mod.read_grid(p)
            self.assertTrue(np.isnan(a[0,0]))
            bad = ref.copy();bad['transform']=from_origin(1,60,30,30)
            with self.assertRaisesRegex(ValueError,'Incompatible'):
                mod.read_grid(p,bad)

if __name__ == '__main__': unittest.main()
