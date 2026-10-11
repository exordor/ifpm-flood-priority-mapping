#!/usr/bin/env python3
"""Build the Goslar ReviewMap QGIS package for mentor/presentation use."""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "bin/package/build_goslar_qgis_full_audit.py"
spec = importlib.util.spec_from_file_location("goslar_full_builder", TEMPLATE)
q = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = q
spec.loader.exec_module(q)

COMPACT_KEYS = {
    "priority",
    "flood_hazard",
    "sediment",
    "landuse_asm",
    "environmental",
    "socioeconomic",
    "rainfall",
    "twi",
    "distance_drainage",
    "soil_k",
    "ls_factor",
    "c_factor",
    "land_use_pressure",
    "clms_vegetation_loss",
    "built_agri_road",
    "population",
    "built_infrastructure",
    "road_access",
    "original_project_focus_extent",
    "boundary",
    "lbeg_mining_rights",
    "osm_mining_points",
    "osm_mining_areas",
    "hwrm_flood_hazard",
    "affected_locations_2017",
}


def relaunch() -> int:
    q.OUT_DIR.mkdir(parents=True, exist_ok=True)
    command = [str(q.QGIS_PYTHON), str(Path(__file__).resolve())]
    return subprocess.run(command, cwd=q.OUT_DIR, env=q.qgis_environment(), check=False).returncode


def configure() -> None:
    q.OUT_DIR = ROOT / "outputs/goslar_qgis_review"
    q.STYLE_DIR = q.OUT_DIR / "styles"
    q.MANIFEST = q.OUT_DIR / "manifest.csv"
    q.VALIDATION = q.OUT_DIR / "validation.json"
    q.README = q.OUT_DIR / "README.txt"
    q.PORTABLE_DIR = ROOT / "exports/qgis_packages/goslar/ReviewMap"
    q.PROJECT_NAME = "IFPM_Goslar_ReviewMap.qgz"
    q.SITE_KEY = "goslar"
    q.__file__ = str(Path(__file__).resolve())
    layers = tuple(
        replace(
            layer,
            visible=layer.key
            in {"priority", "original_project_focus_extent", "boundary", "hwrm_flood_hazard", "affected_locations_2017"},
        )
        for layer in q.GOSLAR_LAYERS
        if layer.key in COMPACT_KEYS
    )
    q.GOSLAR_LAYERS = layers
    q.GOSLAR_SITE = {
        **q.GOSLAR_SITE,
        "name": "Goslar official WRRL reference - ReviewMap presentation package",
        "project_file": q.PROJECT_NAME,
        "layers": layers,
    }
    q.portable_readme_text = lambda: (
        "IFPM Goslar ReviewMap QGIS package\n\n"
        "Open IFPM_Goslar_ReviewMap.qgz directly in QGIS 3.44 or later. This version keeps "
        "the priority result, five weighted criteria, selected scored components, the original "
        "project focus anchor, WRRL reference boundary, 2017 flood impacts and emergency response (approximate locations), mining context, and HWRM context. It "
        "omits terrain intermediates and other audit-only layers. The orange dashed original "
        "focus anchor is visible, has weight 0, and must be contained by any future adopted "
        "Goslar study boundary. It is not a catchment, municipal boundary, or observed "
        "inundation footprint.\n"
    )
    q.write_readme = lambda: q.README.write_text(
        "IFPM Goslar ReviewMap QGIS package\n\n"
        "Open IFPM_Goslar_ReviewMap.qgz. This version keeps the priority result, five weighted criteria, "
        "selected scored components, the original project focus anchor, boundary, mining context, and HWRM context. It omits terrain "
        "intermediates and other audit-only layers. The FullAudit processing chain remains in "
        "outputs/goslar_qgis_full_audit/IFPM_Goslar_FullAudit.qgz.\n",
        encoding="utf-8",
    )


def main() -> int:
    if os.environ.get("IFPM_QGIS_RUNTIME") != "1":
        return relaunch()
    configure()
    rows, readback = q.build_projects()
    q.write_manifest(rows)
    q.write_readme()
    validation = q.validate_package(readback)
    q.build_portable_zip(q.PORTABLE_DIR, q.PORTABLE_DIR.with_suffix(".zip"))
    q.refresh_managed_package_index()
    print(
        f"wrote Goslar ReviewMap QGIS project with {validation['manifest_layer_count']} layers to "
        f"{q.OUT_DIR.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
