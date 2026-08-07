from __future__ import annotations

import importlib.util
import csv
import math
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin/package/build_peru_integrated_briefing_board.py"


def load_board_module():
    if not SCRIPT.exists():
        raise AssertionError(f"board builder is missing: {SCRIPT}")
    spec = importlib.util.spec_from_file_location("build_peru_integrated_briefing_board", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load board builder: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PeruIntegratedBriefingBoardTest(unittest.TestCase):
    def test_layout_is_three_to_two_and_top_level_sections_do_not_overlap(self):
        module = load_board_module()

        self.assertEqual(module.CANVAS_SIZE, (3600, 2400))
        module.validate_layout(module.PANEL_BOXES, module.CANVAS_SIZE)
        self.assertEqual(
            list(module.PANEL_BOXES),
            ["header", "inputs", "priority", "diagnostics", "criteria", "table", "footer"],
        )

    def test_data_strength_rows_are_ordered_and_compact(self):
        module = load_board_module()
        raw_rows = [
            {
                "criterion_id": criterion_id,
                "display_name": display_name,
                "main_weight": weight,
                "implementation": f"source implementation for {criterion_id}",
                "source_evidence": f"source evidence for {criterion_id}",
                "coverage_within_boundary": coverage,
                "known_limit": f"source limitation for {criterion_id}",
            }
            for criterion_id, display_name, weight, coverage in (
                ("socioeconomic", "Socioeconomic exposure indicator", "0.08", "0.999999"),
                ("environmental", "Environmental context indicator (ES)", "0.12", "1.0"),
                ("landuse_asm", "Land use / mining", "0.20", "1.0"),
                ("sediment", "Sediment / erosion", "0.25", "0.951101"),
                ("flood_hazard", "Flood-conditioning indicator (FH)", "0.35", "0.99988"),
            )
        ]

        rows = module.build_data_strength_rows(raw_rows)

        self.assertEqual(
            [row["criterion_id"] for row in rows],
            ["flood_hazard", "sediment", "landuse_asm", "environmental", "socioeconomic"],
        )
        self.assertEqual(rows[0]["weight"], "0.35")
        self.assertEqual(rows[1]["coverage"], "95.11%")
        self.assertEqual(rows[0]["implementation"], "source implementation for flood_hazard")
        self.assertEqual(rows[0]["evidence"], module.PUBLIC_DATA_SUMMARY["flood_hazard"])
        self.assertEqual(rows[1]["limitation"], module.PUBLIC_LIMITATION_SUMMARY["sediment"])
        self.assertTrue(all(len(row["implementation"]) <= 125 for row in rows))
        self.assertTrue(all(len(row["limitation"]) <= 320 for row in rows))

        public_copy = " ".join(row["limitation"] for row in rows).lower()
        for term in ("screening", "scoreable", "diagnostic", "provisional", "unscored", "claim level"):
            self.assertNotIn(term, public_copy)

    def test_data_strength_rejects_duplicate_or_invalid_numeric_rows(self):
        module = load_board_module()
        valid = [
            {
                "criterion_id": criterion_id,
                "display_name": criterion_id,
                "main_weight": weight,
                "implementation": "implementation",
                "source_evidence": "source evidence",
                "known_limit": "limitation",
                "coverage_within_boundary": "1.0",
            }
            for criterion_id, weight in (
                ("flood_hazard", "0.35"),
                ("sediment", "0.25"),
                ("landuse_asm", "0.20"),
                ("environmental", "0.12"),
                ("socioeconomic", "0.08"),
            )
        ]

        with self.assertRaisesRegex(ValueError, "duplicate"):
            module.build_data_strength_rows(valid + [valid[0]])

        invalid = [dict(row) for row in valid]
        invalid[0]["coverage_within_boundary"] = str(math.nan)
        with self.assertRaisesRegex(ValueError, "coverage"):
            module.build_data_strength_rows(invalid)

    def test_first_review_build_declares_png_and_manifest_only(self):
        module = load_board_module()

        output_names = {path.name for path in module.OUTPUTS}
        self.assertEqual(
            output_names,
            {"peru_integrated_briefing_board.png", "manifest.csv"},
        )
        self.assertEqual(len(module.INPUTS), 19)

    def test_public_result_counts_match_current_spatial_and_class_definitions(self):
        module = load_board_module()

        summary = module.result_summary()
        events = module.sinpad_counts()

        self.assertEqual(summary["mining_points_inside"], 2)
        self.assertEqual(summary["mining_records_nearby"], 11)
        # Supervisor-spec weights shrink the High class versus the retained v02 weights.
        self.assertAlmostEqual(summary["high_area_km2"], 164.8008, places=4)
        self.assertEqual(summary["very_high_area_km2"], 0.0)
        self.assertEqual(events["all_high"], 0)
        self.assertEqual(events["all_comparable"], 12)
        self.assertEqual(events["flood_high"], 0)
        self.assertEqual(events["flood_comparable"], 1)

    def test_current_inputs_build_png_and_lineage_manifest(self):
        module = load_board_module()

        module.main()

        module.validate_output(module.OUT_PNG)
        with module.OUT_MANIFEST.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        by_role = {row["role"]: row for row in rows}
        output = by_role["integrated_briefing_board_png"]
        self.assertEqual(output["sha256"], module.sha256(module.OUT_PNG))
        self.assertEqual(output["claim_level"], "sensitivity_scenario")
        self.assertIn("governed_figure_chain_manifest", by_role)
        self.assertIn("sinpad_event_records", by_role)
        self.assertIn("study_area_manifest", by_role)
        self.assertIn("study_area_geometry", by_role)
        self.assertIn("population_by_priority_class", by_role)
        self.assertIn("mining_evidence_manifest", by_role)
        self.assertIn("mining_reference_points", by_role)
        self.assertIn("integrated_briefing_board_builder", by_role)


if __name__ == "__main__":
    unittest.main()
