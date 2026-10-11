from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

from shapely.geometry import Point, box


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv/bin/python"
SCRIPT = ROOT / "bin/acquire/pull_goslar_mining_overlay.py"
CHAIN = ROOT / "bin/factors/run_goslar_pim_chain.py"


def load_module():
    spec = importlib.util.spec_from_file_location("pull_goslar_mining_overlay", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_chain_module():
    spec = importlib.util.spec_from_file_location("goslar_chain_for_mining_test", CHAIN)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {CHAIN}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GoslarMiningOverlayTest(unittest.TestCase):
    def test_query_radius_covers_the_entire_focus_buffer(self):
        """Catches an around-query that omits the corners of the context buffer."""
        module = load_module()
        focus = box(0, 0, 4_000, 6_000)
        context = focus.buffer(12_000)
        radius = module.query_radius_for_context(focus, context)
        center = focus.centroid
        self.assertGreater(radius, 15_000)
        for x, y in (
            (context.bounds[0], context.bounds[1]),
            (context.bounds[0], context.bounds[3]),
            (context.bounds[2], context.bounds[1]),
            (context.bounds[2], context.bounds[3]),
        ):
            self.assertLessEqual(center.distance(Point(x, y)), radius)

    def test_relation_geometry_and_mining_type_are_preserved(self):
        """Catches Rammelsberg-like areas being reduced to a misleading centroid."""
        module = load_module()
        element = {
            "type": "relation",
            "id": 2468275,
            "members": [
                {
                    "type": "way",
                    "role": "outer",
                    "geometry": [
                        {"lon": 10.4180, "lat": 51.8800},
                        {"lon": 10.4240, "lat": 51.8800},
                        {"lon": 10.4240, "lat": 51.8840},
                        {"lon": 10.4180, "lat": 51.8840},
                        {"lon": 10.4180, "lat": 51.8800},
                    ],
                }
            ],
        }
        geometry = module.osm_element_geometry(element)
        self.assertEqual(geometry.geom_type, "Polygon")
        self.assertGreater(geometry.area, 0)
        self.assertEqual(
            module.classify_osm_tags({"industrial": "mine", "landuse": "industrial"}),
            "mine",
        )

    def test_catalog_keeps_mining_context_outside_pim_score(self):
        """Catches accidental promotion of context evidence into PIM scoring."""
        completed = subprocess.run(
            [str(PYTHON), str(SCRIPT), "--catalog-only"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        catalog = json.loads(completed.stdout)
        self.assertEqual(catalog["dataset_id"], "goslar_mining_context_overlay")
        self.assertEqual(catalog["claim_level"], "context_evidence")
        self.assertFalse(catalog["enters_pim_score"])
        self.assertEqual(catalog["overlay_radius_m"], 12000)
        self.assertEqual(
            {source["provider"] for source in catalog["sources"]},
            {"LBEG/NIBIS", "OpenStreetMap/Overpass"},
        )

    def test_chain_catalog_declares_mining_as_external_overlay(self):
        """Catches the model silently treating mining context as a sixth criterion."""
        completed = subprocess.run(
            [str(PYTHON), str(CHAIN), "--catalog-only"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        catalog = json.loads(completed.stdout)
        self.assertEqual(catalog["mining_role"], "external context overlay only")
        self.assertFalse(catalog["mining_enters_pim_score"])

    def test_missing_external_overlay_does_not_block_pim_lineage(self):
        """Catches an optional context layer becoming a hard model dependency."""
        module = load_chain_module()
        missing = ROOT / "outputs/does_not_exist/mining_overlay.gpkg"
        self.assertEqual(
            module.optional_lineage_record(missing),
            {
                "path": "outputs/does_not_exist/mining_overlay.gpkg",
                "exists": False,
            },
        )


if __name__ == "__main__":
    unittest.main()
