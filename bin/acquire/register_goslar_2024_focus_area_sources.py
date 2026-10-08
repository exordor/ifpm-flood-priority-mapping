#!/usr/bin/env python3
"""Register the three provided Goslar 2024 focus-area source files."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TMP_DIR = ROOT / "tmp"
DEST_DIR = ROOT / "data/validation/goslar_harz_2024_focus_area/source_materials"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


SOURCES: list[dict[str, Any]] = [
    {
        "source_id": "qgis_project",
        "kind": "qgis_project",
        "source_filename": "ZDIN-2024.qgz",
        "stored_filename": "ZDIN-2024.goslar_catchment.qgz",
        "title": "ZDIN-2024 QGIS project for the Goslar flood catchment and sensor network",
        "author": "Supervisor (ZDIN-ZLW)",
        "date": "2024-04-25",
        "software": "QGIS 3.22.7",
        "evidence_role": "project context: drainage basin layer references, sensor CSV reference and layout definitions",
    },
    {
        "source_id": "zlw_catchment_map_pdf",
        "kind": "pdf_map",
        "source_filename": "ZLW2024.04.24Einzugs gebeit & sensors.pdf",
        "stored_filename": "ZLW2024.04.24_catchment_and_sensors.pdf",
        "title": "ZLW sensors and catchment map (QGIS print export)",
        "author": "Mareike Bothe-Fiekert",
        "date": "2023-06-12",
        "software": "QGIS 3.22.7",
        "evidence_role": "mapped drainage basin, sensor locations and water feature context",
    },
    {
        "source_id": "zdin_study_area_slide",
        "kind": "slide_image",
        "source_filename": "image (1).png",
        "stored_filename": "ZDIN_goslar_2017flood_intended_study_area.png",
        "title": "ZDIN slide: Goslar 2017 flood catchment and intended study area",
        "author": "ZDIN",
        "date": "unknown",
        "software": "unknown",
        "evidence_role": "2017 flood catchment sub-basins, intended sensor study area and source attribution",
    },
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--register", action="store_true")
    args = parser.parse_args()
    if not args.register:
        print(json.dumps({"focus_area_id": "goslar_harz_2024_focus_extent", "sources": SOURCES}, ensure_ascii=False, indent=2))
        return

    DEST_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for source in SOURCES:
        source_path = TMP_DIR / source["source_filename"]
        if not source_path.is_file():
            raise FileNotFoundError(f"source file missing: {source_path}")
        destination = DEST_DIR / source["stored_filename"]
        if not destination.exists():
            shutil.copy2(source_path, destination)
        records.append(
            {
                **source,
                "path": str(destination.relative_to(ROOT)),
                "size_bytes": destination.stat().st_size,
                "sha256": sha256_file(destination),
            }
        )
    manifest = {
        "focus_area_id": "goslar_harz_2024_focus_extent",
        "focus_area_name": "Goslar 2017 flood catchment and intended sensor study area, Harz, Lower Saxony, Germany",
        "claim_level": "validation_candidate",
        "enters_pim_score": False,
        "access_date": date.today().isoformat(),
        "sources": records,
        "registration_status": "complete",
        "next_stage": "build evidence packet and spatial scope check",
    }
    manifest_path = ROOT / "outputs/goslar_harz_2024_focus_area/source_registration_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
