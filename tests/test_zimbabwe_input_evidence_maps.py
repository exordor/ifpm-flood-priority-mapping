from __future__ import annotations

import csv
import importlib.util
import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin/visualize/export_zimbabwe_input_evidence_maps.py"


def load_module():
    spec = importlib.util.spec_from_file_location("export_zimbabwe_input_evidence_maps", SCRIPT)
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


class ZimbabweInputEvidenceMapsTest(unittest.TestCase):
    def test_current_evidence_set_matches_implemented_components(self):
        module = load_module()
        self.assertEqual((module.MAIN_12_ROWS, module.MAIN_12_COLUMNS), (4, 3))
        factors = {spec.slug for spec in module.RASTER_SPECS} | {module.CATEGORY_SPEC.slug}
        self.assertEqual(len(factors), 17)
        self.assertIn("rainfall_climatology", factors)
        self.assertNotIn("soil_erosion_composite", factors)
        self.assertIn("mineral_reference_proximity", factors)
        self.assertIn("land_cover_pressure", factors)
        self.assertIn("protected_area_context", factors)
        self.assertIn("road_access_proximity", factors)
        self.assertIn("soil_k_factor", factors)
        self.assertIn("distance_to_roads", factors)
        self.assertIn("distance_to_water_features", factors)
        source_text = " ".join(str(path).lower() for path in module.INPUTS)
        self.assertNotIn("top20", source_text)
        self.assertNotIn("equal_active", source_text)
        exporter_source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn('OUT_DIR.glob("zimbabwe_*_evidence_panel_no_title_caption.*")', exporter_source)
        self.assertIn("temporary.replace(path)", exporter_source)
        self.assertNotIn("historical K source window requires correction", exporter_source)

    def test_peru_aligned_factors_share_order_and_palette_semantics(self):
        module = load_module()
        zimbabwe_specs = {spec.slug: spec for spec in module.RASTER_SPECS}
        peru_specs = {
            spec.slug: spec
            for spec in (*module.base.RASTER_SPECS, *module.base.VECTOR_DISTANCE_SPECS)
        }

        for slug in module.base.PERU_MAIN_12_FACTOR_ORDER:
            if slug == module.CATEGORY_SPEC.slug:
                continue
            self.assertIn(slug, zimbabwe_specs)
            self.assertIn(slug, peru_specs)
            self.assertEqual(zimbabwe_specs[slug].colors, peru_specs[slug].colors, slug)

    @WRITES_OUTPUTS
    def test_current_inputs_generate_individual_maps_panels_and_index(self):
        module = load_module()
        module.main()
        with module.INDEX.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 42)
        self.assertEqual(len({row["factor"] for row in rows if row.get("factor")}), 17)
        for row in rows:
            path = ROOT / row["figure_path"]
            self.assertTrue(path.exists(), path)
            self.assertGreater(path.stat().st_size, 0, path)
        aligned = module.OUT_DIR / "zimbabwe_peru_aligned_main_12_evidence_panel_no_title_caption.png"
        self.assertTrue(aligned.exists())
        aligned_row = next(row for row in rows if row.get("panel") == "peru_aligned_main_12" and row["figure_format"] == "png")
        self.assertEqual(
            aligned_row["factors"],
            "; ".join(module.base.PERU_MAIN_12_FACTOR_ORDER),
        )
        self.assertEqual(aligned_row["missing_factors"], "")
        self.assertTrue((module.OUT_DIR / "zimbabwe_flood_sediment_direct_evidence_panel_no_title_caption.png").exists())
        self.assertTrue((module.OUT_DIR / "zimbabwe_land_environment_access_direct_evidence_panel_no_title_caption.png").exists())
        self.assertTrue((module.OUT_DIR / "zimbabwe_supporting_diagnostics_evidence_panel_no_title_caption.png").exists())
        self.assertFalse((module.OUT_DIR / "zimbabwe_current_input_evidence_panel_no_title_caption.png").exists())
        self.assertTrue((module.INDIVIDUAL_DIR / "zimbabwe_evidence_soil_k_factor_no_title_caption.png").exists())
        self.assertFalse((module.INDIVIDUAL_DIR / "zimbabwe_evidence_soil_erosion_composite_no_title_caption.png").exists())
        flood_sediment = next(
            row for row in rows
            if row.get("panel") == "flood_sediment_direct" and row["figure_format"] == "png"
        )
        self.assertEqual(
            flood_sediment["factors"],
            "rainfall_climatology; twi; distance_to_drainage; soil_k_factor; ls_factor; c_factor",
        )

    @WRITES_OUTPUTS
    def test_claim_levels_and_coverage_are_governed(self):
        module = load_module()
        module.main()
        with module.INDEX.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertLessEqual({row["claim_level"] for row in rows}, {"diagnostic_only", "sensitivity_scenario"})
        individual = [
            row for row in rows
            if row.get("factor") and row["factor"] != "esa_worldcover_2021" and row["figure_format"] == "png"
        ]
        self.assertTrue(all(float(row["valid_fraction_within_study_area"]) <= 1.0 for row in individual))
        self.assertTrue(all(float(row["valid_fraction_within_study_area"]) > 0.9 for row in individual))


if __name__ == "__main__":
    unittest.main()
