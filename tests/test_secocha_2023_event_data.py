import json
import hashlib
import unittest
from pathlib import Path

import rasterio


ROOT = Path(__file__).resolve().parents[1]


class Secocha2023EventDataTest(unittest.TestCase):
    def test_event_rainfall_native_stacks_and_lineage(self):
        for manifest_path, stack_name, accumulation_name in [
            (
                ROOT / "outputs/secocha_2023_validation/rainfall/event_rainfall_manifest.json",
                ROOT / "data/validation/secocha_2023_validation/rainfall/chirps_v3_daily_event_window/chirps_v3_daily_2023-01-07_2023-02-10_native.tif",
                ROOT / "data/validation/secocha_2023_validation/rainfall/chirps_v3_daily_event_window/chirps_v3_accumulations_to_2023-02-05_native.tif",
            ),
            (
                ROOT / "outputs/secocha_2023_validation/rainfall_rnl/event_rainfall_rnl_manifest.json",
                ROOT / "data/validation/secocha_2023_validation/rainfall/chirps_v3_rnl_daily_event_window/chirps_v3_rnl_daily_2023-01-07_2023-02-10_native.tif",
                ROOT / "data/validation/secocha_2023_validation/rainfall/chirps_v3_rnl_daily_event_window/chirps_v3_rnl_accumulations_to_2023-02-05_native.tif",
            ),
        ]:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["boundary_id"], "secocha_reference_extent")
            self.assertEqual(manifest["event_date"], "2023-02-05")
            self.assertEqual(manifest["claim_level"], "validation_candidate")
            self.assertFalse(manifest["enters_pim_score"])
            self.assertEqual(manifest["native_resolution"]["degrees"], 0.05)
            self.assertIn("Daily totals provide event-window context only", " ".join(manifest["notes"]))
            self.assertEqual(len(manifest["source_files"]), 35)
            self.assertTrue(all(item["source_width"] == 7200 and item["source_height"] == 2400 for item in manifest["source_files"]))
            self.assertTrue(all(abs(item["source_transform"][0]) == 0.05000000074505806 for item in manifest["source_files"]))
            self.assertTrue(manifest["implementation"]["base_script_sha256"])
            self.assertFalse(manifest["source_integrity"]["remote_content_sha256_saved"])
            self.assertTrue(stack_name.exists())
            self.assertTrue(accumulation_name.exists())
            for local in manifest["local_files"]:
                local_path = ROOT / local["path"]
                self.assertEqual(local["sha256"], hashlib.sha256(local_path.read_bytes()).hexdigest())
            with rasterio.open(stack_name) as dataset:
                self.assertEqual(dataset.count, 35)
                self.assertEqual(dataset.width, 3)
                self.assertEqual(dataset.height, 3)
                self.assertEqual(dataset.crs.to_epsg(), 4326)
                self.assertAlmostEqual(dataset.res[0], 0.05, places=3)
            with rasterio.open(accumulation_name) as dataset:
                self.assertEqual(dataset.count, 5)

    def test_sentinel_catalog_has_reproducible_selected_pair_and_quicklooks(self):
        manifest_path = ROOT / "outputs/secocha_2023_validation/satellite_before_after/sentinel_catalog_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["boundary_id"], "secocha_reference_extent")
        self.assertEqual(manifest["claim_level"], "validation_candidate")
        self.assertFalse(manifest["pixel_asset_downloaded"])
        self.assertEqual(manifest["event_time_utc"], "2023-02-05 19:00-19:17Z")
        self.assertIn("sentinel1_grd", manifest["response_counts"])
        self.assertEqual(manifest["response_counts"]["sentinel1_grd"]["number_returned"], 2)
        self.assertEqual(manifest["response_counts"]["sentinel2_l2a"]["number_returned"], 10)
        selected = manifest["selected_scenes"]
        self.assertEqual(len(selected), 7)
        roles = {item["role"] for item in selected}
        self.assertIn("s1_pre", roles)
        self.assertIn("s1_post", roles)
        self.assertIn("s2_pre_event", roles)
        self.assertIn("s2_post_3d", roles)
        for item in selected:
            self.assertTrue(item["stac_item_self"].startswith("https://stac.dataspace.copernicus.eu/v1/"))
        for item in selected:
            if item["collection"] == "sentinel-1-grd":
                self.assertRegex(item["odata_thumbnail_asset_uuid"], r"^[0-9a-f-]{36}$")
        self.assertEqual(len(manifest["quicklooks"]), 7)
        for item in manifest["quicklooks"]:
            self.assertTrue((ROOT / item["path"]).exists())
            self.assertEqual(item["sha256"], hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest())
        for item in manifest["response_files"] + [manifest["selected_scenes_geojson"]]:
            path = ROOT / item["path"]
            self.assertTrue(path.exists())
            self.assertEqual(item["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_sentinel_pixel_downloader_preserves_catalog_boundary_and_asset_contract(self):
        import importlib.util
        import sys

        path = ROOT / "bin/acquire/pull_secocha_sentinel_pixels.py"
        spec = importlib.util.spec_from_file_location("pull_secocha_sentinel_pixels", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        catalog = json.loads(module.CATALOG.read_text(encoding="utf-8"))
        scene_by_role = {item["role"]: item for item in catalog["selected_scenes"]}
        for role, expected in {
            "s2_pre_event": {"B02_10m", "B03_10m", "B04_10m", "B08_10m", "SCL_20m", "safe_manifest", "product_metadata"},
            "s2_post_3d": {"B02_10m", "B03_10m", "B04_10m", "B08_10m", "SCL_20m", "safe_manifest", "product_metadata"},
            "s1_pre": {"vv", "vh", "safe_manifest", "schema-product-vv", "schema-product-vh", "schema-calibration-vv", "schema-calibration-vh", "schema-noise-vv", "schema-noise-vh"},
            "s1_post": {"vv", "vh", "safe_manifest", "schema-product-vv", "schema-product-vh", "schema-calibration-vv", "schema-calibration-vh", "schema-noise-vv", "schema-noise-vh"},
        }.items():
            self.assertEqual(set(module.requested_assets(scene_by_role[role])), expected)
        href = "s3://eodata/Sentinel-2/test/S2.example.SAFE/manifest.safe"
        self.assertEqual(
            module.normalize_key(href),
            "Sentinel-2/test/S2.example.SAFE/manifest.safe",
        )
        self.assertIn("pixels", str(module.DATA_DIR))

    def test_sentinel_quantitative_pixels_are_downloaded_and_hash_registered(self):
        base = ROOT / "outputs/secocha_2023_validation/satellite_before_after"
        for manifest_name, roles, assets in [
            (
                "sentinel_pixel_download_core_s2_manifest.json",
                {"s2_pre_event", "s2_post_3d"},
                {"B02_10m", "B03_10m", "B04_10m", "B08_10m", "SCL_20m", "safe_manifest", "product_metadata"},
            ),
            (
                "sentinel_pixel_download_s1_pair_manifest.json",
                {"s1_pre", "s1_post"},
                {"vv", "vh", "safe_manifest", "schema-product-vv", "schema-product-vh", "schema-calibration-vv", "schema-calibration-vh", "schema-noise-vv", "schema-noise-vh"},
            ),
        ]:
            with (base / manifest_name).open(encoding="utf-8") as handle:
                manifest = json.load(handle)
            self.assertEqual(manifest["event_date"], "2023-02-05")
            self.assertEqual(manifest["boundary_id"], "secocha_reference_extent")
            self.assertEqual(manifest["claim_level"], "validation_candidate")
            self.assertFalse(manifest["enters_pim_score"])
            self.assertTrue(manifest["size_checks_passed"])
            self.assertEqual({item["role"] for item in manifest["downloaded_assets"]}, roles)
            self.assertEqual({item["asset"] for item in manifest["downloaded_assets"]}, assets)
            for item in manifest["downloaded_assets"]:
                path = ROOT / item["path"]
                self.assertEqual(path.stat().st_size, item["bytes"])
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"])

    def test_active_scope_check_does_not_reuse_frozen_peru_boundary(self):
        active_path = ROOT / "outputs/secocha_2023_validation/spatial_scope_check_active.json"
        legacy_path = ROOT / "outputs/secocha_2023_validation/spatial_scope_check.json"
        active = json.loads(active_path.read_text(encoding="utf-8"))
        legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
        self.assertEqual(active["status"], "active_scope_check")
        self.assertEqual(active["current_boundary"]["boundary_id"], "secocha_reference_extent")
        self.assertTrue(active["current_boundary"]["contains_secocha_anchor"])
        self.assertEqual(legacy["status"], "superseded_legacy_check")
        self.assertEqual(legacy["superseded_by"], "outputs/secocha_2023_validation/spatial_scope_check_active.json")

    def test_rainfall_sensitivity_pair_is_explicitly_compared(self):
        comparison_path = ROOT / "outputs/secocha_2023_validation/rainfall/rainfall_sat_vs_rnl_comparison.json"
        csv_path = ROOT / "outputs/secocha_2023_validation/rainfall/rainfall_sat_vs_rnl_comparison.csv"
        comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
        self.assertEqual(comparison["claim_level"], "validation_candidate")
        self.assertFalse(comparison["enters_pim_score"])
        self.assertIn("not independent observed rainfall", comparison["interpretation"])
        windows = {row["window"] for row in comparison["accumulation_rows"]}
        self.assertIn("cum_1d_2023-02-05", windows)
        self.assertIn("cum_7d_2023-01-30_2023-02-05", windows)
        self.assertTrue(csv_path.exists())
        self.assertEqual(comparison["boundary_id"], "secocha_reference_extent")
        self.assertEqual(comparison["event_date"], "2023-02-05")
        self.assertEqual(comparison["local_lineage"]["sat"]["stack"]["sha256"], hashlib.sha256((ROOT / comparison["local_lineage"]["sat"]["stack"]["path"]).read_bytes()).hexdigest())
        self.assertEqual(comparison["local_lineage"]["rnl"]["accumulation"]["sha256"], hashlib.sha256((ROOT / comparison["local_lineage"]["rnl"]["accumulation"]["path"]).read_bytes()).hexdigest())

    def test_rerun_summary_binds_pim_event_and_new_validation_data(self):
        summary_path = ROOT / "outputs/secocha_2023_validation/rerun_validation_summary.json"
        markdown_path = ROOT / "outputs/secocha_2023_validation/rerun_validation_summary.md"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "provisional_validation_rerun")
        self.assertTrue(summary["lineage_checks_passed"])
        self.assertTrue(all(item["status"] == "pass" for item in summary["lineage_checks"]))
        priority = ROOT / summary["pim_rerun"]["priority_raster"]["path"]
        self.assertEqual(summary["pim_rerun"]["priority_raster"]["sha256"], hashlib.sha256(priority.read_bytes()).hexdigest())
        self.assertEqual(summary["pim_rerun"]["quality_assurance_status"], "pass")
        event = summary["historical_event_candidate"]
        valid_cells = event["valid_support_cells"]
        total_cells = event["total_event_cells"]
        self.assertEqual(total_cells, 237)
        self.assertGreater(valid_cells, 0)
        self.assertLess(valid_cells, total_cells)
        self.assertIn(f"valid-support enrichment (n={valid_cells}/{total_cells})", event["high_pim_enrichment_interpretation"])
        markdown = markdown_path.read_text(encoding="utf-8")
        self.assertIn(f"valid support; n={valid_cells}/{total_cells}", markdown)
        self.assertIn("threshold is **0.6**", markdown)
        self.assertIn(f"{total_cells - valid_cells}/{total_cells} event cells are excluded", markdown)
        self.assertIn("not an official 5 February observed footprint", markdown)


if __name__ == "__main__":
    unittest.main()
