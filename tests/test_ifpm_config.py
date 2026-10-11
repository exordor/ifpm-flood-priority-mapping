"""configs/*.yaml are consistent with the ifpm stages and the dataset registry (PyYAML only)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ifpm.config import Config, areas  # noqa: E402

# Stage names each extent method understands (see ifpm/chain.py, expanded.py and rescore.py).
BASIN = {"dem", "slope", "hydrology", "ls_factor", "worldcover_cfactor", "soilgrids_kfactor", "osm_roads",
         "rainfall", "protected_areas", "criteria_stack", "exposure_indicators",
         "environmental_sensitivity", "priority_scenarios", "validate"}
METHOD_STAGES = {
    "basin": BASIN,
    "abzucht": {"prepare", "slope", "hydrology", "ls_factor", "soilgrids_kfactor", "osm_roads", "rainfall",
                "protected_areas", "criteria_stack", "exposure_indicators", "environmental_sensitivity",
                "priority_scenarios", "report", "overlay"},
    "multiriver": {"prepare", "terrain", "landcover", "hydrology", "ls_factor", "soilgrids_kfactor",
                   "osm_roads", "rainfall", "protected_areas", "criteria_stack", "exposure_indicators",
                   "environmental_sensitivity", "priority_scenarios", "comparison", "report"},
    "rescore": {"score"},
}


def dataset_ids(node):
    """Every string in a config that names a datasets.yaml entry."""
    if isinstance(node, dict):
        for value in node.values():
            yield from dataset_ids(value)
    elif isinstance(node, list):
        for value in node:
            yield from dataset_ids(value)
    elif isinstance(node, str):
        yield node


class ConfigTest(unittest.TestCase):
    def test_areas(self):
        self.assertEqual(areas(), ["goslar", "peru_former", "secocha", "zimbabwe"])

    def test_weights_sum_to_one(self):
        for area in areas():
            weights = Config(area)["weights"]
            self.assertAlmostEqual(sum(weights["main"].values()), 1.0, places=9, msg=area)
            for name, parts in weights["components"].items():
                self.assertAlmostEqual(sum(parts.values()), 1.0, places=9, msg=f"{area} {name}")

    def test_extent_stages_and_verify_globs(self):
        for area in areas():
            cfg = Config(area)
            for name in cfg.extents:
                ext = cfg.extent(name)
                unknown = set(ext["stages"]) - METHOD_STAGES[ext["method"]]
                self.assertFalse(unknown, f"{area}/{name}: {unknown}")
                for pattern in ext.get("verify", []):
                    self.assertTrue(pattern.startswith("outputs/"), pattern)

    def test_referenced_datasets_exist_in_registry(self):
        for area in areas():
            cfg = Config(area)
            referenced = {s for s in dataset_ids(cfg.data) if s in cfg.datasets}
            rescore_only = all(cfg.extent(n)["method"] == "rescore" for n in cfg.extents)
            self.assertTrue(referenced or rescore_only, area)  # rescore reads earlier outputs only
            for dataset_id in referenced:
                entry = cfg.entry(dataset_id)
                self.assertTrue("path" in entry or "url" in entry, dataset_id)
                self.assertFalse(Path(entry.get("path", "")).is_absolute(), dataset_id)

    def test_paths_are_inside_workspace(self):
        cfg = Config("goslar")
        for dataset_id, entry in cfg.datasets.items():
            if "path" not in entry:
                continue  # remote source (CHIRPS)
            path = cfg.path(dataset_id, year=2018)
            self.assertTrue(str(path).startswith(str(ROOT)), dataset_id)


if __name__ == "__main__":
    unittest.main()
