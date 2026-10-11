from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin/package/build_goslar_qgis_full_audit.py"
PACKAGE = ROOT / "outputs/goslar_qgis_full_audit"
PORTABLE = ROOT / "exports/qgis_packages/goslar/FullAudit"
GENERATED_PACKAGE_AVAILABLE = (PACKAGE / "validation.json").exists() and PORTABLE.exists()


def load_module():
    spec = importlib.util.spec_from_file_location("build_goslar_qgis_full_audit", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GoslarQgisProjectPackageTest(unittest.TestCase):
    def test_portable_zip_builder_excludes_hidden_files(self):
        """Catches a stale/manual ZIP handoff and macOS metadata leakage."""
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "Portable_Package"
            (package / "layers").mkdir(parents=True)
            (package / "README.txt").write_text("portable\n", encoding="utf-8")
            (package / "layers/data.txt").write_text("layer\n", encoding="utf-8")
            (package / ".DS_Store").write_bytes(b"hidden")
            (package / "layers/._data.txt").write_bytes(b"hidden")
            archive = root / "Portable_Package.zip"

            module.build_portable_zip(package, archive)

            with zipfile.ZipFile(archive) as handle:
                self.assertEqual(
                    set(handle.namelist()),
                    {
                        "Portable_Package/README.txt",
                        "Portable_Package/layers/data.txt",
                    },
                )

    def test_mining_layers_are_external_context_overlays(self):
        """Catches mining context being omitted or mislabeled as a scored criterion."""
        module = load_module()
        by_key = {layer.key: layer for layer in module.GOSLAR_LAYERS}
        for key, layer_name in {
            "lbeg_mining_rights": "lbeg_mining_rights",
            "osm_mining_points": "osm_mining_points",
            "osm_mining_areas": "osm_mining_areas",
        }.items():
            self.assertIn(key, by_key)
            spec = by_key[key]
            self.assertEqual(spec.layer_name, layer_name)
            self.assertEqual(spec.role, "mining_context_overlay")
            self.assertEqual(spec.claim_level, "context_evidence")
            self.assertFalse(spec.visible)
        self.assertNotIn("mining", module.GOSLAR_SITE.get("scored_criteria", ()))

    def test_official_context_layers_are_external_overlays(self):
        """Official context must be visible in QGIS but cannot silently enter PIM scoring."""
        module = load_module()
        by_key = {layer.key: layer for layer in module.GOSLAR_LAYERS}
        expected = {
            "wfd_drainage_basins": ("hydrologic_context", "goslar_wfd_drainage_basins_focus_overlap"),
            "hwrm_flood_hazard": ("flood_hazard_context", "goslar_hwrm_flood_hazard_boundaries_12km"),
            "osm_infrastructure": ("infrastructure_context", "osm_infrastructure_candidates"),
        }
        for key, (role, layer_name) in expected.items():
            self.assertIn(key, by_key)
            spec = by_key[key]
            self.assertEqual(spec.group, module.EXTERNAL_OVERLAY_GROUP)
            self.assertEqual(spec.role, role)
            self.assertEqual(spec.layer_name, layer_name)
            self.assertEqual(spec.claim_level, "context_evidence")
            self.assertFalse(spec.visible)
        scored = set(module.GOSLAR_SITE["scored_criteria"])
        self.assertNotIn("official_hydrology", scored)
        self.assertNotIn("flood_hazard_scenarios", scored)
        self.assertNotIn("infrastructure", scored)

    def test_2017_affected_locations_are_visible_non_scoring_event_evidence(self):
        module = load_module()
        by_key = {layer.key: layer for layer in module.GOSLAR_LAYERS}
        evidence = by_key["affected_locations_2017"]
        self.assertEqual(evidence.group, module.EXTERNAL_OVERLAY_GROUP)
        self.assertEqual(evidence.role, "historical_event_location_evidence")
        self.assertEqual(evidence.layer_name, "affected_location_evidence")
        self.assertEqual(evidence.claim_level, "validation_candidate")
        self.assertTrue(evidence.visible)
        self.assertIn("not a complete inundation footprint", evidence.notes)
        self.assertNotIn("affected_locations_2017", module.GOSLAR_SITE["scored_criteria"])

    def test_original_project_focus_extent_is_a_visible_non_scoring_overlay(self):
        by_key = {layer.key: layer for layer in load_module().GOSLAR_LAYERS}
        focus = by_key["original_project_focus_extent"]
        self.assertEqual(
            focus.name,
            "Original project map focus extent (minimum study-area anchor)",
        )
        self.assertEqual(focus.group, "7. External validation and overlays")
        self.assertEqual(focus.role, "study_area_anchor")
        self.assertEqual(focus.layer_name, "goslar_focus_boundary")
        self.assertEqual(focus.claim_level, "project_layout_reference")
        self.assertTrue(focus.visible)
        self.assertIn("must be contained", focus.notes)

    def test_active_infrastructure_layer_names_and_claims_are_accurate(self):
        """The raster is an OSM proximity input, not a built-up proxy."""
        module = load_module()
        by_key = {layer.key: layer for layer in module.GOSLAR_LAYERS}
        proximity = by_key["built_infrastructure"]
        self.assertEqual(
            proximity.name,
            "Critical infrastructure proximity, OSM facilities (SV component weight 0.30)",
        )
        self.assertEqual(proximity.claim_level, "provisional")
        self.assertIn("Active critical_infrastructure component", proximity.notes)
        self.assertIn("2 km linear decay", proximity.notes)

        source_points = by_key["osm_infrastructure"]
        self.assertEqual(source_points.name, "Critical-infrastructure source points (OSM)")
        self.assertIn("active critical_infrastructure proximity component", source_points.notes)
        self.assertNotIn("excluded from scoring", source_points.notes)

        self.assertEqual(
            module.GOSLAR_SITE["name"],
            "Goslar official WRRL reference - FullAudit processing chain (provisional)",
        )

    def test_configuration_covers_full_chain_with_intermediates(self):
        module = load_module()

        self.assertEqual(module.GOSLAR_SITE["project_crs"], "EPSG:32632")
        roles = [layer.role for layer in module.GOSLAR_LAYERS]
        self.assertEqual(roles.count("priority_result"), 1)
        self.assertEqual(roles.count("criterion"), 5)
        self.assertGreaterEqual(roles.count("input_factor"), 18)

        groups = list(dict.fromkeys(layer.group for layer in module.GOSLAR_LAYERS))
        self.assertEqual(
            groups,
            [
                "1. Priority result",
                "2. Five PIM criteria",
                "3. Terrain and hydrology",
                "4. Erosion factors",
                "5. Rainfall",
                "6. Exposure and environment",
                "7. External validation and overlays",
            ],
        )
        keys = {layer.key for layer in module.GOSLAR_LAYERS}
        for expected in {
            "priority", "flood_hazard", "sediment", "landuse_asm", "environmental",
            "socioeconomic", "elevation", "dem_filled", "slope", "flow_direction",
            "flow_accumulation", "streams", "distance_drainage", "twi", "ls_factor",
            "soil_k", "c_factor", "land_use_pressure", "rainfall", "population",
            "built_infrastructure", "road_access", "water_wetland", "protected_area",
            "clms_vegetation_loss", "built_agri_road",
            "boundary", "natura2000", "roads",
            "original_project_focus_extent",
            "wfd_drainage_basins", "hwrm_flood_hazard", "osm_infrastructure",
        }:
            self.assertIn(expected, keys)

        public_text = " ".join(layer.name for layer in module.GOSLAR_LAYERS).lower()
        self.assertNotIn("mentor", public_text)
        self.assertNotIn("top 20", public_text)
        self.assertNotIn("direct pim", public_text)
        self.assertNotIn("srtm", public_text)

        for spec in module.GOSLAR_LAYERS:
            self.assertTrue((module.ROOT / spec.path).exists(), spec.path)

    def test_direct_scored_layers_expose_weights_in_display_names(self):
        module = load_module()
        by_key = {layer.key: layer for layer in module.GOSLAR_LAYERS}
        expected = {
            "flood_hazard": "PIM weight 0.34",
            "sediment": "PIM weight 0.25",
            "landuse_asm": "PIM weight 0.17",
            "environmental": "PIM weight 0.10",
            "socioeconomic": "PIM weight 0.14",
            "rainfall": "FH component weight 0.35",
            "twi": "FH component weight 0.25",
            "distance_drainage": "FH component weight 0.40",
            "soil_k": "SE component weight 0.25",
            "ls_factor": "SE component weight 0.50",
            "c_factor": "SE component weight 0.25",
            "land_use_pressure": "LU component weight 0.40",
            "clms_vegetation_loss": "LU component weight 0.35",
            "built_agri_road": "LU component weight 0.25",
            "water_wetland": "ES component weight 0.65",
            "protected_area": "ES component weight 0.35",
            "road_access": "SV component weight 0.35",
            "population": "SV component weight 0.35",
            "built_infrastructure": "SV component weight 0.30",
        }
        for key, label in expected.items():
            self.assertIn(key, by_key)
            self.assertIn(label, by_key[key].name)

        # Intermediate terrain products do not carry a direct component weight.
        for key in ("elevation", "dem_filled", "slope", "flow_direction", "flow_accumulation", "streams"):
            self.assertNotIn("weight", by_key[key].name.lower())

    def test_qgis_palettes_match_original_goslar_maps(self):
        module = load_module()
        plot_path = ROOT / "bin/visualize/plot_goslar_pim_overview.py"
        plot_spec = importlib.util.spec_from_file_location("plot_goslar_pim_overview", plot_path)
        self.assertIsNotNone(plot_spec)
        self.assertIsNotNone(plot_spec.loader)
        plot_module = importlib.util.module_from_spec(plot_spec)
        sys.modules[plot_spec.name] = plot_module
        plot_spec.loader.exec_module(plot_module)

        self.assertEqual(module.PRIORITY_COLORS, plot_module.PRIORITY_COLORS)
        self.assertEqual(module.CRITERIA_COLORS, plot_module.CRITERIA_COLORS)
        self.assertEqual(
            module.STANDARD_CLASS_UPPER_BOUNDS,
            tuple(plot_module.PRIORITY_BOUNDS[1:-1]) + (1.0,),
        )
        self.assertEqual(module.STANDARD_CLASS_LABELS, tuple(plot_module.CLASS_LABELS))

    @unittest.skipUnless(GENERATED_PACKAGE_AVAILABLE, "run the Goslar QGIS package builder first")
    def test_generated_qml_uses_original_discrete_color_contract(self):
        module = load_module()
        expected = {
            "priority": tuple(module.PRIORITY_COLORS),
            **{key: tuple(colors) for key, colors in module.CRITERIA_COLORS.items()},
        }
        for layer_key, expected_colors in expected.items():
            for style_root in (PACKAGE / "styles", PORTABLE / "styles"):
                root = ElementTree.fromstring((style_root / f"goslar_{layer_key}.qml").read_bytes())
                shader = root.find(".//colorrampshader")
                self.assertIsNotNone(shader)
                self.assertEqual(shader.attrib["colorRampType"], "DISCRETE")
                self.assertEqual(shader.attrib["clip"], "1")
                items = shader.findall("item")
                self.assertEqual(
                    tuple(float(item.attrib["value"]) for item in items),
                    module.STANDARD_CLASS_UPPER_BOUNDS,
                )
                self.assertEqual(
                    tuple(item.attrib["label"] for item in items),
                    module.STANDARD_CLASS_LABELS,
                )
                self.assertEqual(
                    tuple(item.attrib["color"].lower() for item in items),
                    expected_colors,
                )

    @unittest.skipUnless(GENERATED_PACKAGE_AVAILABLE, "run the Goslar QGIS package builder first")
    def test_original_focus_style_contains_an_explicit_map_label(self):
        style = PACKAGE / "styles/goslar_original_project_focus_extent.qml"
        self.assertTrue(style.exists())
        text = style.read_text(encoding="utf-8")
        self.assertIn("Original project focus extent", text)
        self.assertIn("labeling", text)
        self.assertIn('fontFamily="Arial"', text)
        self.assertNotIn(".AppleSystemUIFont", text)

    @unittest.skipUnless(
        Path("/Applications/QGIS.app").exists()
        or Path("/Applications/QGIS-LTR.app").exists(),
        "QGIS is not installed",
    )
    def test_qgis_build_and_layer_qa(self):
        validator = ROOT / "bin/validate/validate_goslar_qgis_layer_rendering.py"
        subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
        subprocess.run([sys.executable, str(validator)], cwd=ROOT, check=True)
        report = json.loads(
            (PACKAGE / "layer_qa/layer_qa.json").read_text(encoding="utf-8")
        )
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["pass_count"], 37)

    @unittest.skipUnless(GENERATED_PACKAGE_AVAILABLE, "run the Goslar QGIS package builder first")
    def test_generated_project_is_portable_within_workspace(self):
        project_path = PACKAGE / "IFPM_Goslar_FullAudit.qgz"
        self.assertTrue(project_path.exists())
        with zipfile.ZipFile(project_path) as archive:
            qgs_names = [name for name in archive.namelist() if name.endswith(".qgs")]
            self.assertEqual(len(qgs_names), 1)
            project_xml = archive.read(qgs_names[0]).decode("utf-8")
        self.assertNotIn("/Users/jlw/", project_xml)
        self.assertIn("<Paths>", project_xml)
        self.assertIn('<Absolute type="bool">false</Absolute>', project_xml)
        self.assertIn('source="../', project_xml)

    @unittest.skipUnless(GENERATED_PACKAGE_AVAILABLE, "run the Goslar QGIS package builder first")
    def test_manifest_records_valid_layers_and_styles(self):
        # The boundary GPKG write is non-deterministic (SQLite internals), and
        # the focus-boundary test re-exports it. Rebuild the package first so
        # the manifest hashes match the live source files regardless of test
        # order.
        subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
        manifest = PACKAGE / "manifest.csv"
        self.assertTrue(manifest.exists())
        with manifest.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 37)
        self.assertTrue(all(row["load_status"] == "valid" for row in rows))
        self.assertTrue(all((ROOT / row["source_path"]).exists() for row in rows))
        for row in rows:
            source = ROOT / row["source_path"]
            portable = PORTABLE / row["portable_source_path"]
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), row["source_sha256"])
            self.assertEqual(
                hashlib.sha256(portable.read_bytes()).hexdigest(),
                row["portable_sha256"],
            )
        styled = [row for row in rows if row["style_path"]]
        self.assertEqual(len(styled), 37)
        self.assertTrue(all((PACKAGE / row["style_path"]).exists() for row in styled))

        validation = json.loads((PACKAGE / "validation.json").read_text(encoding="utf-8"))
        self.assertEqual(validation["status"], "package_integrity_valid")
        self.assertEqual(
            validation["generator_sha256"],
            hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
        )
        self.assertEqual(len(validation["qgis_readback"]), 2)
        self.assertTrue(all(item["read_success"] for item in validation["qgis_readback"]))
        self.assertTrue(all(not item["invalid_layers"] for item in validation["qgis_readback"]))

    @unittest.skipUnless(GENERATED_PACKAGE_AVAILABLE, "run the Goslar QGIS package builder first")
    def test_portable_export_is_self_contained(self):
        module = load_module()
        portable = module.PORTABLE_DIR
        self.assertEqual({path.name for path in portable.glob("*.qgz")}, {"IFPM_Goslar_FullAudit.qgz"})
        with (portable / "manifest.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertTrue(all((portable / row["portable_source_path"]).exists() for row in rows))
        self.assertTrue(all(row["portable_sha256"] for row in rows))
        self.assertNotIn("source_path", rows[0])

        for project in portable.glob("*.qgz"):
            with zipfile.ZipFile(project) as archive:
                self.assertEqual(len(archive.namelist()), 1)
                qgs = next(name for name in archive.namelist() if name.endswith(".qgs"))
                project_xml = archive.read(qgs).decode("utf-8")
            self.assertNotIn("jlw", project_xml)
            self.assertNotIn("../", project_xml)
            self.assertNotIn("mentor", project_xml.lower())


if __name__ == "__main__":
    unittest.main()
