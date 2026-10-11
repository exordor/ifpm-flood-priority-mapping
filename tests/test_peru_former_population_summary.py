from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "bin/analysis/summarize_peru_former_population_by_pim_class.py"


def load_module():
    spec = importlib.util.spec_from_file_location("summarize_peru_former_population_by_pim_class", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PeruPopulationSummaryTest(unittest.TestCase):
    def test_population_counts_are_sum_aggregated_to_pim_grid(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "population.tif"
            profile = {
                "driver": "GTiff",
                "width": 2,
                "height": 2,
                "count": 1,
                "dtype": "float32",
                "crs": "EPSG:32718",
                "transform": from_origin(0.0, 20.0, 10.0, 10.0),
                "nodata": -9999.0,
            }
            with rasterio.open(source, "w", **profile) as dst:
                dst.write(np.array([[1.0, 2.0], [3.0, 4.0]], dtype="float32"), 1)

            target_profile = {
                "width": 1,
                "height": 1,
                "crs": "EPSG:32718",
                "transform": from_origin(0.0, 20.0, 20.0, 20.0),
            }
            result = module.aggregate_population_to_pim_grid(source, target_profile)

        self.assertEqual(result.shape, (1, 1))
        self.assertAlmostEqual(float(result[0, 0]), 10.0, places=5)


if __name__ == "__main__":
    unittest.main()
