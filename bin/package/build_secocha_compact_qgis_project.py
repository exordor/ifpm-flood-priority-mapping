#!/usr/bin/env python3
"""Build the Secocha ReviewMap QGIS package for mentor/presentation use."""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "bin/package/build_peru_secocha_qgis_project_package.py"
spec = importlib.util.spec_from_file_location("secocha_full_builder", TEMPLATE)
builder = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)
q = builder.q

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
    "land_pressure",
    "bare_soil",
    "built_agri_road",
    "population",
    "built",
    "road_access",
    "boundary",
    "event_footprint",
    "event_huaico",
    "event_mudflow",
    "mining",
}


def relaunch() -> int:
    q.OUT_DIR.mkdir(parents=True, exist_ok=True)
    command = [str(q.QGIS_PYTHON), str(Path(__file__).resolve())]
    return subprocess.run(command, cwd=q.OUT_DIR, env=q.qgis_environment(), check=False).returncode


def configure() -> None:
    q.OUT_DIR = ROOT / "outputs/peru_secocha_qgis_project_package_compact"
    q.STYLE_DIR = q.OUT_DIR / "styles"
    q.MANIFEST = q.OUT_DIR / "manifest.csv"
    q.VALIDATION = q.OUT_DIR / "validation.json"
    q.README = q.OUT_DIR / "README.txt"
    q.PORTABLE_DIR = ROOT / "exports/qgis_packages/secocha/ReviewMap"
    q.PROJECT_NAME = "IFPM_Peru_Secocha_ReviewMap.qgz"
    layers = tuple(
        replace(
            layer,
            visible=layer.key
            in {"priority", "boundary", "event_footprint", "event_huaico", "event_mudflow", "mining"},
        )
        for layer in q.GOSLAR_LAYERS
        if layer.key in COMPACT_KEYS
    )
    q.GOSLAR_LAYERS = layers
    q.GOSLAR_SITE = {
        **q.GOSLAR_SITE,
        "name": "Peru: Secocha 2023 prototype - ReviewMap presentation package",
        "project_file": q.PROJECT_NAME,
        "layers": layers,
    }
    q.__file__ = str(Path(__file__).resolve())
    review_readme = (
        "IFPM Peru Secocha ReviewMap QGIS package\n\n"
        "Open IFPM_Peru_Secocha_ReviewMap.qgz. This version keeps the priority result, five weighted criteria, "
        "selected scored components, boundary, Map 7 event candidates, and mining context. It omits terrain "
        "intermediates and other audit-only layers. The FullAudit processing chain remains in "
        "outputs/peru_secocha_qgis_project_package/IFPM_Peru_Secocha_FullAudit.qgz.\n",
    )
    review_readme = "".join(review_readme)
    q.write_readme = lambda: q.README.write_text(review_readme, encoding="utf-8")
    inherited_portable_export = q.build_portable_export

    def build_review_portable(rows):
        project = inherited_portable_export(rows)
        (q.PORTABLE_DIR / "README.txt").write_text(review_readme, encoding="utf-8")
        return project

    q.build_portable_export = build_review_portable


def main() -> int:
    if os.environ.get("IFPM_QGIS_RUNTIME") != "1":
        return relaunch()
    configure()
    rows, readback = q.build_projects()
    q.write_manifest(rows)
    q.write_readme()
    validation = q.validate_package(readback)
    q.build_portable_zip(q.PORTABLE_DIR, q.PORTABLE_DIR.with_suffix(".zip"))
    print(
        f"wrote Secocha ReviewMap QGIS project with {validation['manifest_layer_count']} layers to "
        f"{q.OUT_DIR.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
