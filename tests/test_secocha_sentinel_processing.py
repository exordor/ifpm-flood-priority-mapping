from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

import rasterio


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin/analysis/process_secocha_sentinel_validation.py"
OUT = ROOT / "outputs/secocha_2023_validation/satellite_before_after/processed"


def load_module():
    spec = importlib.util.spec_from_file_location("process_secocha_sentinel_validation", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SecochaSentinelProcessingTest(unittest.TestCase):
    def test_processing_contract_and_outputs_exist(self):
        module = load_module()
        self.assertEqual(module.PRE_ROLE, "s2_pre_event")
        self.assertEqual(module.POST_ROLE, "s2_post_3d")
        self.assertEqual(module.SCL_VALID_CLASSES, {4, 5, 6, 7})
        manifest_path = OUT / "s2_optical_change_qa.json"
        self.assertTrue(manifest_path.exists())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["claim_level"], "validation_candidate")
        self.assertFalse(manifest["enters_pim_score"])
        self.assertEqual(manifest["dates"], {"before": "2023-02-03", "after": "2023-02-08"})
        self.assertIn("not an official observed event footprint", " ".join(manifest["limitations"]))
        for name in (
            "s2_ndwi_before_10m.tif",
            "s2_ndwi_after_10m.tif",
            "s2_surface_water_before_candidate_10m.tif",
            "s2_surface_water_after_candidate_10m.tif",
            "s2_new_surface_water_candidate_10m.tif",
            "s2_lost_surface_water_candidate_10m.tif",
        ):
            path = OUT / name
            self.assertTrue(path.exists(), name)
            with rasterio.open(path) as dataset:
                self.assertEqual(dataset.crs.to_epsg(), 32718)
                self.assertAlmostEqual(dataset.res[0], 10, places=6)


if __name__ == "__main__":
    unittest.main()
