from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/goslar_official_hydrology_and_flood_data"


def load_module():
    path = ROOT / "bin/acquire/pull_goslar_official_hydrology_flood_infrastructure.py"
    spec = importlib.util.spec_from_file_location("goslar_official_sources", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GoslarOfficialSourcesTest(unittest.TestCase):
    def test_registry_and_lineage_are_registered(self):
        registry = ROOT / "context/docs/data-management/registry/goslar_official_hydrology_flood_infrastructure.md"
        lineage = OUT / "source_lineage.json"
        self.assertTrue(registry.exists())
        self.assertTrue(lineage.exists())
        payload = json.loads(lineage.read_text())
        self.assertEqual(payload["dataset_id"], "goslar_official_hydrology_flood_infrastructure_v1")
        self.assertFalse(payload["enters_pim_score"])
        for key in ("basins", "river_segments", "oker_hazard", "innerste_hazard", "nlwkn_2017_report", "osm_infrastructure"):
            self.assertIn(key, payload["sources"])
            self.assertIn("sha256", payload["sources"][key])

    def test_official_layers_exist_and_do_not_enter_score(self):
        for name in (
            "goslar_wfd_drainage_basins_focus_overlap.gpkg",
            "goslar_hwrm_flood_hazard_boundaries_12km.gpkg",
        ):
            path = OUT / name
            self.assertTrue(path.exists(), name)
            self.assertGreater(path.stat().st_size, 1024)


if __name__ == "__main__":
    unittest.main()
