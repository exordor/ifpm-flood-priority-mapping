import json
import os
import subprocess
import unittest
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv/bin/python"
SCRIPT = ROOT / "bin/acquire/export_goslar_focus_boundary.py"


# Regenerating these files writes into the real outputs/; the default run stays read-only.
WRITES_OUTPUTS = unittest.skipUnless(
    os.environ.get("IFPM_WRITE_OUTPUTS") == "1",
    "regenerates files under outputs/; set IFPM_WRITE_OUTPUTS=1 to run",
)


class GoslarFocusBoundaryTest(unittest.TestCase):
    @WRITES_OUTPUTS
    def test_exports_goslar_focus_boundary_gpkg(self):
        completed = subprocess.run(
            [str(PYTHON), str(SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        gpkg = ROOT / "outputs/goslar_focus_boundary/goslar_focus_boundary.gpkg"
        self.assertTrue(gpkg.exists())
        gdf = gpd.read_file(gpkg)
        self.assertEqual(len(gdf), 1)
        self.assertEqual(gdf.iloc[0]["boundary_id"], "goslar_focus_extent_v1")
        self.assertEqual(gdf.iloc[0]["claim_level"], "prototype_only")
        manifest = json.loads(
            (ROOT / "outputs/goslar_focus_boundary/goslar_focus_boundary_manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["boundary_id"], "goslar_focus_extent_v1")
        self.assertEqual(manifest["extent_wgs84"], [10.3646, 51.8544, 10.4194, 51.9089])
        self.assertAlmostEqual(manifest["geo_area_km2"], 22.882, places=3)
        self.assertTrue(gdf.geometry.iloc[0].equals_exact(box(10.3646, 51.8544, 10.4194, 51.9089), 1e-9))


if __name__ == "__main__":
    unittest.main()
