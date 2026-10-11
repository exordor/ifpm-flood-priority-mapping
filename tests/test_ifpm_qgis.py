"""QGIS packages: the layer contract in configs/*.yaml, and read-only checks of the built packages.

Ported from the tests of the old bin/package QGIS builders. Building needs the QGIS
application (python -m ifpm qgis <area>); these tests only read.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ifpm import qgis, scoring  # noqa: E402
from ifpm.config import Config  # noqa: E402

OVERLAY_GROUP = "7. External validation and overlays"


def layers(area: str, package: str = "FullAudit") -> dict:
    spec = qgis.package_spec(Config(area), package, ROOT)
    return {layer["key"]: layer for layer in spec["layers"]}


def built_packages():
    """(area, package, workspace dir, portable dir, project file) of every configured package."""
    for area in ("goslar", "secocha"):
        for name, pkg in Config(area)["qgis"]["packages"].items():
            yield area, name, ROOT / pkg["out_dir"], ROOT / pkg["portable_dir"], pkg["project_file"]


class LayerContractTest(unittest.TestCase):
    def test_full_chain_with_intermediates(self):
        for area, crs in (("goslar", "EPSG:32632"), ("secocha", "EPSG:32718")):
            with self.subTest(area):
                self.assertEqual(Config(area)["qgis"]["project_crs"], crs)
                by_key = layers(area)
                roles = [layer["role"] for layer in by_key.values()]
                self.assertEqual(roles.count("priority_result"), 1)
                self.assertEqual(roles.count("criterion"), 5)
                self.assertGreaterEqual(roles.count("input_factor"), 18)
                for layer in by_key.values():
                    self.assertTrue((ROOT / layer["path"]).exists(), layer["path"])
                text = " ".join(layer["name"] for layer in by_key.values()).lower()
                for word in ("mentor", "top 20", "direct pim"):
                    self.assertNotIn(word, text)

    def test_scored_layers_show_their_weights(self):
        cfg = Config("goslar")
        by_key = layers("goslar")
        for criterion, weight in cfg["weights"]["main"].items():
            self.assertIn(f"PIM weight {weight:.2f}", by_key[criterion]["name"])
        expected = {"rainfall": "FH component weight 0.35", "twi": "FH component weight 0.25",
                    "distance_drainage": "FH component weight 0.40", "ls_factor": "SE component weight 0.50",
                    "soil_k": "SE component weight 0.25", "c_factor": "SE component weight 0.25",
                    "built_infrastructure": "SV component weight 0.30"}
        for key, label in expected.items():
            self.assertIn(label, by_key[key]["name"])
        for key in ("elevation", "dem_filled", "slope", "flow_direction", "flow_accumulation", "streams"):
            self.assertNotIn("weight", by_key[key]["name"].lower())

    def test_context_layers_are_non_scoring_overlays(self):
        goslar = layers("goslar")
        for key in ("lbeg_mining_rights", "osm_mining_points", "osm_mining_areas",
                    "wfd_drainage_basins", "hwrm_flood_hazard", "osm_infrastructure"):
            self.assertEqual(goslar[key]["group"], OVERLAY_GROUP)
            self.assertEqual(goslar[key]["claim_level"], "context_evidence")
            self.assertFalse(goslar[key]["visible"])
        self.assertIn("not proof of active", goslar["lbeg_mining_rights"]["notes"].lower())
        self.assertFalse({"event_footprint", "event_huaico", "event_mudflow"} & set(goslar))
        secocha = layers("secocha")
        for key in ("boundary", "original_a7367", "event_footprint", "event_huaico", "event_mudflow",
                    "mining", "field_anchors", "response_locations"):
            self.assertEqual(secocha[key]["group"], OVERLAY_GROUP)
        self.assertIn("not verified active", secocha["mining"]["notes"].lower())

    def test_goslar_anchor_and_event_evidence_are_visible(self):
        goslar = layers("goslar")
        focus = goslar["original_project_focus_extent"]
        self.assertEqual((focus["role"], focus["claim_level"]), ("study_area_anchor", "project_layout_reference"))
        self.assertTrue(focus["visible"])
        self.assertIn("must be contained", focus["notes"])
        evidence = goslar["affected_locations_2017"]
        self.assertEqual(evidence["role"], "historical_event_location_evidence")
        self.assertTrue(evidence["visible"])
        self.assertIn("not a complete inundation footprint", evidence["notes"])

    def test_review_maps_are_subsets(self):
        for area, audit_only in (("goslar", {"dem_filled", "flow_direction", "flow_accumulation", "streams"}),
                                 ("secocha", {"s2_ndwi_before", "s2_new_surface_water", "minedu_schools_2023",
                                              "ingemmet_mining_rights"})):
            with self.subTest(area):
                full, review = layers(area), layers(area, "ReviewMap")
                self.assertLess(set(review), set(full))
                self.assertFalse(audit_only & set(review))
                self.assertTrue({"priority", "boundary", *scoring_criteria()} <= set(review))
                visible = set(Config(area)["qgis"]["packages"]["ReviewMap"]["visible"])
                self.assertEqual({k for k, layer in review.items() if layer["visible"]}, visible)

    def test_secocha_lineage_token_is_filled(self):
        notes = layers("secocha")["minedu_schools_2023"]["notes"]
        self.assertNotIn("{proxy_lineage}", notes)
        self.assertRegex(notes, r"source_manifest_sha256=[0-9a-f]{64}\.")

    def test_class_edges_match_the_score_classes(self):
        self.assertEqual(qgis.STANDARD_CLASS_UPPER_BOUNDS, tuple(scoring.CLASS_EDGES[1:-1]) + (1.0,))


def scoring_criteria():
    return ("flood_hazard", "sediment", "landuse_asm", "environmental", "socioeconomic")


class PortableZipTest(unittest.TestCase):
    def test_zip_excludes_hidden_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "Portable_Package"
            (package / "layers").mkdir(parents=True)
            (package / "README.txt").write_text("portable\n", encoding="utf-8")
            (package / "layers/data.txt").write_text("layer\n", encoding="utf-8")
            (package / ".DS_Store").write_bytes(b"hidden")
            (package / "layers/._data.txt").write_bytes(b"hidden")
            archive = qgis.build_portable_zip(package, Path(tmp) / "Portable_Package.zip")
            with zipfile.ZipFile(archive) as handle:
                self.assertEqual(set(handle.namelist()),
                                 {"Portable_Package/README.txt", "Portable_Package/layers/data.txt"})


def project_xml(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith(".qgs")]
        assert len(names) == 1, path
        return archive.read(names[0]).decode("utf-8")


@unittest.skipUnless((ROOT / "exports/qgis_packages/package_index.json").exists(), "QGIS packages not built")
class BuiltPackagesTest(unittest.TestCase):
    def test_validation_and_readback(self):
        for area, name, out_dir, _, project in built_packages():
            with self.subTest(f"{area}/{name}"):
                self.assertTrue((out_dir / project).exists())
                validation = json.loads((out_dir / "validation.json").read_text(encoding="utf-8"))
                self.assertEqual(validation["status"], "package_integrity_valid")
                self.assertEqual(validation["manifest_layer_count"], len(layers(area, name)))
                self.assertTrue(all(r["read_success"] and not r["invalid_layers"] for r in validation["qgis_readback"]))

    def test_workspace_projects_use_relative_paths(self):
        for area, name, out_dir, _, project in built_packages():
            with self.subTest(f"{area}/{name}"):
                xml = project_xml(out_dir / project)
                self.assertNotIn(str(ROOT), xml)
                self.assertIn('<Absolute type="bool">false</Absolute>', xml)
                self.assertIn(OVERLAY_GROUP, xml)

    def test_portable_packages_are_self_contained_and_zipped(self):
        index = json.loads((ROOT / "exports/qgis_packages/package_index.json").read_text(encoding="utf-8"))
        for area, name, _, portable, project in built_packages():
            with self.subTest(f"{area}/{name}"):
                xml = project_xml(portable / project)
                self.assertNotIn("../", xml)
                self.assertNotIn(str(Path.home()), xml)
                if area == "goslar":  # labels need a font that exists on Windows too
                    self.assertIn('fontFamily="Arial"', xml)
                with (portable / "manifest.csv").open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertNotIn("source_path", rows[0])
                for row in rows:
                    data = (portable / row["portable_source_path"]).read_bytes()
                    self.assertEqual(hashlib.sha256(data).hexdigest(), row["portable_sha256"])
                files = {p.relative_to(portable).as_posix(): p for p in portable.rglob("*") if p.is_file()}
                self.assertFalse(any(n.endswith(".aux.xml") for n in files))
                archive_path = portable.with_suffix(".zip")
                with zipfile.ZipFile(archive_path) as archive:
                    archived = {n.removeprefix(f"{portable.name}/"): n for n in archive.namelist()}
                    self.assertEqual(set(archived), set(files))
                    for relative, path in files.items():
                        self.assertEqual(archive.read(archived[relative]), path.read_bytes(), relative)
                record = index[f"{area}_{name.lower()}"]
                self.assertEqual(record["zip_sha256"], hashlib.sha256(archive_path.read_bytes()).hexdigest())
                self.assertEqual(record["layer_count"], len(rows))

    def test_discrete_classes_in_styles(self):
        expected = {"priority": tuple(qgis.PRIORITY_COLORS),
                    **{key: tuple(colors) for key, colors in qgis.CRITERIA_COLORS.items()}}
        for area, name, out_dir, portable, _ in built_packages():
            for key, colors in expected.items():
                for style_dir in (out_dir / "styles", portable / "styles"):
                    with self.subTest(f"{area}/{name}/{key}"):
                        shader = ElementTree.fromstring((style_dir / f"{area}_{key}.qml").read_bytes()).find(".//colorrampshader")
                        self.assertEqual((shader.attrib["colorRampType"], shader.attrib["clip"]), ("DISCRETE", "1"))
                        items = shader.findall("item")
                        self.assertEqual(tuple(float(i.attrib["value"]) for i in items), qgis.STANDARD_CLASS_UPPER_BOUNDS)
                        self.assertEqual(tuple(i.attrib["label"] for i in items), qgis.STANDARD_CLASS_LABELS)
                        self.assertEqual(tuple(i.attrib["color"].lower() for i in items), colors)


if __name__ == "__main__":
    unittest.main()
