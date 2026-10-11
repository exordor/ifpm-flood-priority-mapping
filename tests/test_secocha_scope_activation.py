import hashlib
import json
import subprocess
import unittest
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv/bin/python"
SCRIPT = ROOT / "bin/analysis/activate_secocha_research_area.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PeruSecochaScopeActivationTest(unittest.TestCase):
    def test_activation_creates_new_boundary_and_freezes_previous_area(self):
        completed = subprocess.run(
            [str(PYTHON), str(SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

        active = json.loads(
            (ROOT / "outputs/secocha_scope_activation/active_peru_research_area.json").read_text()
        )
        self.assertEqual(
            active["active_area"]["boundary_id"],
            "secocha_reference_extent",
        )
        self.assertEqual(
            active["frozen_previous_area"]["boundary_id"],
            "peru_former",
        )
        self.assertEqual(active["frozen_previous_area"]["status"], "frozen_baseline")
        output_scope = json.loads(
            (
                ROOT
                / "outputs/secocha_pim_chain/scope_manifest.json"
            ).read_text()
        )
        self.assertEqual(
            output_scope["boundary_id"], "secocha_reference_extent"
        )
        self.assertEqual(
            output_scope["frozen_output_root"], "outputs/peru_former_pim_chain"
        )

        boundary = gpd.read_file(
            ROOT / "outputs/secocha_boundary/secocha_boundary.gpkg",
            layer="secocha_active_boundary",
        ).to_crs("EPSG:32718")
        self.assertEqual(len(boundary), 1)
        self.assertAlmostEqual(float(boundary.geometry.area.iloc[0] / 1e6), 30.0, places=3)
        self.assertTrue(boundary.geometry.iloc[0].covers(Point(695121, 8232667)))
        self.assertFalse(bool(boundary.iloc[0]["event_footprint"]))
        self.assertFalse(bool(boundary.iloc[0]["catchment_boundary"]))

        frozen = json.loads(
            (ROOT / "outputs/peru_former_pim_chain/FROZEN_BASELINE.json").read_text()
        )
        self.assertEqual(frozen["status"], "frozen_baseline")
        for artifact in frozen["key_artifacts"].values():
            path = ROOT / artifact["path"]
            self.assertTrue(path.exists())
            self.assertEqual(sha256(path), artifact["sha256"])

        audit = json.loads(
            (ROOT / "outputs/secocha_scope_activation/secocha_data_coverage_audit.json").read_text()
        )
        self.assertTrue(audit["local_coverage"]["worldcover"]["covers_active_extent"])
        self.assertTrue(audit["local_coverage"]["worldpop"]["covers_active_extent"])
        self.assertEqual(audit["local_coverage"]["srtm_dem"]["required_tile"], "S16W074.SRTMGL1.hgt.zip")
        self.assertFalse(audit["local_coverage"]["old_ingemmet_subset"]["reusable"])
        self.assertFalse(audit["local_coverage"]["old_sernanp_subset"]["reusable"])


if __name__ == "__main__":
    unittest.main()
