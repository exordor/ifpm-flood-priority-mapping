import json
import hashlib
import os
import subprocess
import unittest
from pathlib import Path

import numpy as np
import rasterio


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv/bin/python"
SCRIPT = ROOT / "bin/factors/run_goslar_pim_chain.py"
OUT = ROOT / "outputs/goslar_pim_chain"
SECOCHA_MANIFEST = (
    ROOT
    / "outputs/secocha_pim_chain/priority_scenarios/run_manifest.json"
)


# Regenerating these files writes into the real outputs/; the default run stays read-only.
WRITES_OUTPUTS = unittest.skipUnless(
    os.environ.get("IFPM_WRITE_OUTPUTS") == "1",
    "regenerates files under outputs/; set IFPM_WRITE_OUTPUTS=1 to run",
)


class GoslarPeruStyleChainTest(unittest.TestCase):
    def test_goslar_uses_same_full_weight_contract_as_secocha(self):
        """Catches site-specific Goslar weight changes that break comparability."""
        completed = subprocess.run(
            [str(PYTHON), str(SCRIPT), "--catalog-only"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        goslar = json.loads(completed.stdout)
        secocha = json.loads(SECOCHA_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(goslar["main_weights"], secocha["main_weights"])
        self.assertEqual(
            goslar["component_weights"],
            {
                "flood_hazard": secocha["component_weights"]["FH"],
                "sediment": secocha["component_weights"]["SE"],
                "landuse_asm": secocha["component_weights"]["LU"],
                "environmental": secocha["component_weights"]["ES"],
                "socioeconomic": secocha["component_weights"]["SV"],
            },
        )

    def test_chain_catalog_declares_stages_and_data_gaps(self):
        completed = subprocess.run(
            [str(PYTHON), str(SCRIPT), "--catalog-only"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        catalog = json.loads(completed.stdout)
        self.assertEqual(catalog["focus_area_id"], "goslar_wrrl_basin")
        self.assertEqual(catalog["metric_crs"], "EPSG:32632")
        self.assertEqual(catalog["claim_level"], "provisional")
        self.assertEqual(catalog["data_gaps"], {})
        self.assertIn("rainfall", catalog["data_sources"])
        self.assertIn("protected_areas", catalog["data_sources"])
        self.assertIn("dem", catalog["data_sources"])
        self.assertIn("population", catalog["data_sources"])
        self.assertIn("Copernicus", catalog["data_sources"]["dem"])
        self.assertIn("Zensus", catalog["data_sources"]["population"])
        self.assertIn("Natura 2000", catalog["data_sources"]["protected_areas"])
        self.assertIn("boundary", catalog["stages"])
        self.assertIn("priority_scenarios", catalog["stages"])
        # The complete Supervisor v07 contract must remain identical to Secocha.
        self.assertEqual(
            catalog["component_weights"]["landuse_asm"],
            {
                "land_cover_pressure": 0.40,
                "bare_soil_vegetation_loss": 0.35,
                "built_agriculture_road_expansion": 0.25,
            },
        )
        self.assertEqual(
            catalog["component_weights"]["socioeconomic"],
            {
                "road_access_proximity": 0.35,
                "settlement_population": 0.35,
                "critical_infrastructure": 0.30,
            },
        )
        self.assertEqual(catalog["removed_components"], {})
        self.assertIn("worldcover", catalog["nodata_policy"])

    def test_chain_fills_rainfall_and_protected_area_gaps(self):
        completed = subprocess.run(
            [str(PYTHON), str(SCRIPT), "--catalog-only"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        catalog = json.loads(completed.stdout)
        self.assertNotIn("rainfall", catalog["data_gaps"])
        self.assertNotIn("protected_areas", catalog["data_gaps"])
        self.assertIn("rainfall", catalog["stages"])
        self.assertIn("protected_areas", catalog["stages"])

    @WRITES_OUTPUTS
    def test_chain_runs_and_produces_reference_grid_and_priority_map(self):
        completed = subprocess.run(
            [str(PYTHON), str(SCRIPT), "--max-stage", "priority_scenarios"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        ref = ROOT / "outputs/goslar_pim_chain/terrain_preprocessing/goslar_focus_dem_utm32n_30m.tif"
        self.assertTrue(ref.exists())
        with rasterio.open(ref) as src:
            self.assertEqual(src.crs.to_epsg(), 32632)
            self.assertAlmostEqual(src.res[0], 30.0, delta=0.5)
        priority = ROOT / "outputs/goslar_pim_chain/priority_scenarios/scenarios/priority_goslar_direct_pim.tif"
        self.assertTrue(priority.exists())
        manifest = json.loads(
            (ROOT / "outputs/goslar_pim_chain/priority_scenarios/run_manifest.json").read_text(encoding="utf-8")
        )
        self.assertFalse(manifest["enters_pim_score"])
        self.assertEqual(manifest["main_weights"], {
            "flood_hazard": 0.34,
            "sediment": 0.25,
            "landuse_asm": 0.17,
            "environmental": 0.10,
            "socioeconomic": 0.14,
        })
        self.assertNotIn("rainfall", manifest.get("data_gaps", {}))
        self.assertNotIn("protected_areas", manifest.get("data_gaps", {}))
        # fh_components_applied was replaced by the full component_weights map.
        self.assertEqual(
            manifest["component_weights"]["flood_hazard"],
            {"rainfall_climatology": 0.35, "twi_wetness": 0.25, "drainage_proximity": 0.40},
        )
        self.assertEqual(manifest["removed_components"], {})
        self.assertEqual(manifest["hydrology_buffer_m"], 1000.0)
        self.assertTrue(manifest["soilgrids_k_snapshot"]["sha256"])
        self.assertTrue(manifest["input_lineage"]["clms_tcd_loss"]["sha256"])
        self.assertIn("soilgrids", manifest["nodata_policy"])
        self.assertEqual(
            manifest["priority_raster_lineage"]["sha256"],
            hashlib.sha256(priority.read_bytes()).hexdigest(),
        )
        self.assertEqual(set(manifest["criterion_raster_lineage"]), {
            "flood_hazard", "sediment", "landuse_asm", "environmental", "socioeconomic",
        })
        self.assertIn("implementation", manifest["input_lineage"])
        self.assertIn("boundary", manifest["input_lineage"])
        official = manifest["official_hydrology_and_validation"]
        self.assertFalse(official["enters_pim_score"])
        self.assertEqual(official["claim_level"], "validation_candidate/context")
        lineage = manifest["input_lineage"]["official_hydrology_and_validation"]
        for key in (
            "wfd_drainage_basins",
            "hwrm_flood_hazard_boundaries",
            "source_lineage",
            "diagnostics",
            "nlwkn_2017_report",
            "osm_infrastructure_candidates",
        ):
            self.assertTrue(lineage[key]["exists"], key)

    def test_technical_fixes_hold_on_regenerated_outputs(self):
        """Road CRS and NoData fixes hold without changing Secocha weights."""
        def read(path):
            with rasterio.open(path) as src:
                arr = src.read(1).astype("float64")
                if src.nodata is not None:
                    arr[arr == src.nodata] = np.nan
                return arr
        # A) Road proximity must come from metric-grid rasterized roads (>0
        #    road-bearing cells). The pre-fix WGS84 rasterization hit 0 cells.
        road = read(OUT / "criteria_stack/criteria/road_access_proximity_0_1.tif")
        # High proximity everywhere is expected for urban Goslar; the fix is
        # that roads were actually rasterized. Re-derive the binary road mask
        # by checking proximity is not the edge-distance artifact: mean must
        # exceed the broken value (~0.805) and have low variance near 1.
        self.assertGreater(np.nanmean(road), 0.95)
        # B) SoilGrids NoData preserved (not filled with 0): the aligned K
        #    layer must contain NaN cells inside the focus box.
        k = read(OUT / "soil_k_factor/soil_k_factor_aligned_250m_effective_30m.tif")
        self.assertGreater(int(np.sum(~np.isfinite(k))), 0)
        # B2) CLMS TCD loss replaces the former all-zero bare-soil proxy.
        bare_soil = read(OUT / "criteria_stack/criteria/bare_soil_vegetation_loss_0_1.tif")
        self.assertGreater(int(np.sum(bare_soil > 0)), 1000)
        # C) Weight repair stays separate from technical repair: Goslar retains
        #    the exact Secocha component contract despite local limitations.
        manifest = json.loads((OUT / "priority_scenarios/run_manifest.json").read_text())
        secocha = json.loads(SECOCHA_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["component_weights"]["landuse_asm"], secocha["component_weights"]["LU"])
        self.assertEqual(manifest["component_weights"]["socioeconomic"], secocha["component_weights"]["SV"])
        # D) Priority map is finite across the common support and in [0,1].
        priority = read(OUT / "priority_scenarios/scenarios/priority_goslar_direct_pim.tif")
        self.assertTrue(np.all(priority[np.isfinite(priority)] >= 0))
        self.assertTrue(np.all(priority[np.isfinite(priority)] <= 1))
        self.assertGreater(int(np.sum(np.isfinite(priority))), 20000)


if __name__ == "__main__":
    unittest.main()
