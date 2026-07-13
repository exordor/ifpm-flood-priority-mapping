from __future__ import annotations

import importlib.util
import csv
import hashlib
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCAL_MAP_OUTPUTS_READY = all(
    path.exists()
    for path in (
        ROOT / "outputs/slide_ready_figures/peru_pim_criteria_maps/index.csv",
        ROOT / "outputs/slide_ready_figures/peru_direct_weight_priority_maps/index.csv",
        ROOT / "outputs/slide_ready_figures/peru_pim_contribution_map/index.csv",
        ROOT / "outputs/slide_ready_figures/peru_evidence_overlays/index.csv",
    )
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class PeruSlideMapSourceTest(unittest.TestCase):
    def test_pim_socioeconomic_map_describes_current_source(self):
        module = load_module(
            "export_peru_pim_criteria_maps",
            ROOT / "bin/visualize/export_peru_pim_criteria_maps.py",
        )
        criterion = next(item for item in module.CRITERIA if item.slug == "socioeconomic")

        self.assertIn("WorldPop", criterion.data_basis)
        self.assertIn("building", criterion.data_basis.lower())
        self.assertNotIn("road/access proximity only", criterion.limitation.lower())

    def test_context_exporter_covers_all_new_socioeconomic_layers(self):
        module = load_module(
            "export_peru_exposure_context_maps",
            ROOT / "bin/visualize/export_peru_exposure_context_maps.py",
        )

        self.assertEqual(
            {item.slug for item in module.MAP_SPECS},
            {
                "population_exposure",
                "built_infrastructure_exposure",
                "exposure_indicators",
                "poverty_context",
                "health_service_remoteness",
            },
        )
        self.assertTrue(all("exposure_indicators" in str(item.source_raster) for item in module.MAP_SPECS))

    @unittest.skipUnless(LOCAL_MAP_OUTPUTS_READY, "requires ignored local slide-ready outputs")
    def test_slide_ready_indexes_bind_figures_to_source_checksums(self):
        indexes = (
            ROOT / "outputs/slide_ready_figures/peru_pim_criteria_maps/index.csv",
        )
        for path in indexes:
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(rows, path)
            for row in rows:
                source = ROOT / (row.get("source_raster") or row["source"])
                digest = hashlib.sha256(source.read_bytes()).hexdigest()
                self.assertEqual(row.get("source_sha256"), digest, path)

    @unittest.skipUnless(LOCAL_MAP_OUTPUTS_READY, "requires ignored local slide-ready outputs")
    def test_direct_weight_map_index_uses_the_current_direct_scenario_raster(self):
        path = ROOT / "outputs/slide_ready_figures/peru_direct_weight_priority_maps/index.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        expected_source = ROOT / (
            "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/"
            "priority_mentor_peru_direct_pim.tif"
        )
        expected_hash = hashlib.sha256(expected_source.read_bytes()).hexdigest()
        selection_source = ROOT / (
            "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/"
            "top20_mentor_peru_direct_pim.tif"
        )
        selection_hash = hashlib.sha256(selection_source.read_bytes()).hexdigest()

        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row["source"] == str(expected_source.relative_to(ROOT)) for row in rows))
        self.assertTrue(all(row["source_sha256"] == expected_hash for row in rows))
        self.assertTrue(all("direct_weight" in row["map_type"] for row in rows))
        top20_rows = [row for row in rows if "top20" in row["map_type"]]
        self.assertEqual(len(top20_rows), 2)
        self.assertTrue(all(row["selection_sha256"] == selection_hash for row in top20_rows))

    @unittest.skipUnless(LOCAL_MAP_OUTPUTS_READY, "requires ignored local slide-ready outputs")
    def test_contribution_map_index_binds_all_five_criterion_hashes(self):
        path = ROOT / "outputs/slide_ready_figures/peru_pim_contribution_map/index.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 2)
        for row in rows:
            source_paths = row["source_rasters"].split(";")
            recorded = dict(item.split(":", 1) for item in row["source_sha256"].split(";"))
            self.assertEqual(len(source_paths), 5)
            for source_path in source_paths:
                source = ROOT / source_path
                criterion = source.stem.removesuffix("_0_1")
                self.assertEqual(recorded[criterion], hashlib.sha256(source.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
