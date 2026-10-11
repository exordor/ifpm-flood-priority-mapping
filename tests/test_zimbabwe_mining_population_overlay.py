from __future__ import annotations

import csv
import importlib.util
import os
import sys
import unittest
from pathlib import Path

import geopandas as gpd
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin/visualize/export_zimbabwe_mining_population_overlay.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "export_zimbabwe_mining_population_overlay", SCRIPT
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# Regenerating these files writes into the real outputs/; the default run stays read-only.
WRITES_OUTPUTS = unittest.skipUnless(
    os.environ.get("IFPM_WRITE_OUTPUTS") == "1",
    "regenerates files under outputs/; set IFPM_WRITE_OUTPUTS=1 to run",
)


class ZimbabweMiningPopulationOverlayTest(unittest.TestCase):
    def test_overlay_uses_footprints_and_population_context(self):
        module = load_module()

        self.assertIn("global_mining_polygons_v2", str(module.MINING_FOOTPRINTS))
        self.assertIn("worldpop_2020_zimbabwe", str(module.POPULATION))
        script_text = SCRIPT.read_text(encoding="utf-8").lower()
        self.assertNotIn("top20", script_text)
        self.assertNotIn("geometry.centroid", script_text)

    @WRITES_OUTPUTS
    def test_export_is_traceable_and_boundary_clipped(self):
        module = load_module()
        module.main()

        for path in module.OUTPUTS:
            self.assertTrue(path.exists(), path)

        footprints = gpd.read_file(module.CLIPPED_FOOTPRINTS)
        self.assertEqual(len(footprints), 6)
        self.assertTrue((footprints.to_crs("EPSG:32735").geometry.area > 0).all())

        with module.INDEX.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["mapped_mining_footprints"] == "6" for row in rows))
        self.assertTrue(all(row["evidence_role"] == "independent_context" for row in rows))
        self.assertTrue(all("not official mining titles" in row["note"] for row in rows))
        self.assertTrue(all(float(row["pim_coverage_fraction"]) < 1.0 for row in rows))
        self.assertTrue(all(float(row["population_valid_fraction"]) < 1.0 for row in rows))
        self.assertTrue(all("upper decile" in row["population_contour_basis"] for row in rows))
        self.assertTrue(all("non-exhaustive" in row["note"] for row in rows))
        self.assertTrue(
            all("500 m Gaussian kernel" in row["population_display_method"] for row in rows)
        )
        _, _, population, inside = module.read_boundary_population()
        self.assertGreater(int(population.size), 0)
        self.assertGreater(float(population[np.isfinite(population)].max()), max(module.POPULATION_LEVELS))
        self.assertGreater(int(inside.sum()), int(np.isfinite(population).sum()))
        source_rows = module.source_assessment_rows()
        mining_row = next(row for row in source_rows if row["source"] == "Global Mining Polygons v2")
        self.assertIn("non-exhaustive", mining_row["limitation"])
        ghsl_row = next(row for row in source_rows if row["source"].startswith("GHSL"))
        self.assertIn("visual clutter", ghsl_row["limitation"])


if __name__ == "__main__":
    unittest.main()
