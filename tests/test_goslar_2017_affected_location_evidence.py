from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

import geopandas as gpd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/goslar_2017_affected_location_evidence"
GPKG = OUT / "goslar_2017_affected_location_evidence.gpkg"
MANIFEST = OUT / "manifest.json"
SUMMARY = OUT / "location_consistency_summary.json"
CSV = OUT / "affected_location_pim_samples.csv"
FIGURE = OUT / "goslar_2017_affected_locations_vs_pim.png"


class Goslar2017AffectedLocationEvidenceTest(unittest.TestCase):
    def test_output_is_location_evidence_not_a_flood_footprint(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "provisional")
        self.assertEqual(manifest["claim_level"], "validation_candidate")
        self.assertEqual(manifest["validation_type"], "location_based_historical_event_consistency_check")
        self.assertFalse(manifest["enters_pim_score"])
        self.assertFalse(manifest["is_complete_flood_extent"])
        self.assertEqual(manifest["event_peak_date"], "2017-07-26")
        self.assertEqual(manifest["location_count"], 9)
        self.assertEqual(manifest["high_threshold"], 0.60)
        self.assertEqual(manifest["very_high_threshold"], 0.80)
        self.assertEqual(manifest["classification_policy"]["moderate"], [0.4, 0.6])

    def test_points_preserve_source_position_and_pim_lineage(self):
        points = gpd.read_file(GPKG, layer="affected_location_evidence")
        self.assertEqual(len(points), 9)
        self.assertEqual(points.crs.to_epsg(), 32632)
        self.assertEqual(points["location_id"].nunique(), 9)
        required = {
            "location_id", "location_name", "evidence_type", "evidence_group", "impact_summary",
            "source_org", "source_url", "source_locator", "coordinate_source",
            "position_precision", "pim_value", "pim_class", "distance_to_high_m",
            "max_pim_100m", "enters_pim_score",
        }
        self.assertTrue(required.issubset(points.columns), points.columns)
        self.assertTrue(points.geometry.is_valid.all())
        self.assertTrue(points["pim_value"].between(0, 1).all())
        self.assertTrue(points["max_pim_100m"].between(0, 1).all())
        self.assertTrue((points["distance_to_high_m"] >= 0).all())
        self.assertTrue((points["distance_to_high_m"] % 10 == 0).all())
        self.assertTrue(points["distance_method"].str.contains("rounded to 10 m").all())
        self.assertFalse(points["enters_pim_score"].astype(bool).any())
        self.assertTrue(points["source_url"].str.startswith("https://").all())
        self.assertFalse(points["position_precision"].str.strip().eq("").any())

    def test_summary_uses_valid_support_and_declares_metric_boundary(self):
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
        self.assertEqual(summary["high_threshold"], 0.60)
        self.assertEqual(summary["very_high_threshold"], 0.80)
        self.assertEqual(summary["sample_count"], 9)
        self.assertEqual(summary["valid_pim_sample_count"], 9)
        self.assertEqual(
            summary["prohibited_metrics"],
            ["flood_extent_recall", "flooded_nonflooded_accuracy", "intersection_over_union", "false_positive_flood_area"],
        )
        self.assertIn("descriptive", summary["interpretation"].lower())
        self.assertNotIn("validated", summary["interpretation"].lower())

    def test_csv_and_figure_are_complete(self):
        with CSV.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 9)
        self.assertTrue(FIGURE.is_file())
        self.assertGreater(FIGURE.stat().st_size, 50_000)


class DiagnosticNumericsTest(unittest.TestCase):
    def test_nodata_threshold_and_group_weighting(self):
        import importlib.util
        import tempfile
        from unittest.mock import patch
        import numpy as np
        import rasterio
        from rasterio.transform import from_origin
        from shapely.geometry import Point
        spec = importlib.util.spec_from_file_location("evidence", ROOT / "bin/analysis/build_goslar_2017_affected_location_evidence.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            raster=folder / "pim.tif"
            with rasterio.open(raster,"w",driver="GTiff",height=1,width=4,count=1,
                    dtype="float64",crs="EPSG:32632",transform=from_origin(0,30,30,30),nodata=-9999) as ds:
                ds.write(np.array([[0.6, 0.5999998, -9999, 0.2]]),1)
            config=folder / "config.json"
            config.write_text(json.dumps({"radii_m":[0,30],"local_background_radius_m":1000,
                "reach_groups":{"a":["one","two","four"],"b":["three"]}}))
            points=gpd.GeoDataFrame({"location_id":["one","two","three","four"],
                "evidence_type":["damage"]*4,"pim_cell_id":["0:0","0:1","0:3","0:0"],"pim_value":[0.6,0.6,0.2,0.6],
                "pim_class":["High","Moderate","Moderate","High"]},
                geometry=[Point(15,15),Point(45,15),Point(105,15),Point(15,15)],crs="EPSG:32632")
            with patch.multiple(module,ROOT=folder,PIM=raster,OUT=folder,CONFIG=config):
                module.write_diagnostics(points)
            with (folder / "radius_group_background_comparison.csv").open() as handle:
                rows=list(csv.DictReader(handle))
            lookup={(r["group"],int(r["radius_m"])):r for r in rows}
            self.assertEqual(float(lookup["all_records",0]["high_present_fraction"]),1/2)
            self.assertEqual(float(lookup["equal_weight_reach_mean",0]["high_present_fraction"]),0.25)
            self.assertEqual(int(lookup["background_all_valid",0]["records"]),3)
            self.assertEqual(float(lookup["background_all_valid",30]["high_present_fraction"]),2/3)


if __name__ == "__main__":
    unittest.main()
