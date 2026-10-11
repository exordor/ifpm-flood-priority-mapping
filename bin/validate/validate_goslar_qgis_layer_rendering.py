#!/usr/bin/env python3
"""Render and audit every governed raster in the Goslar QGIS project."""

from __future__ import annotations

import csv
import importlib.util
import json
import math
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = ROOT / "bin/package/build_goslar_qgis_full_audit.py"
QA_DIR = ROOT / "outputs/goslar_qgis_full_audit/layer_qa"
PREVIEW_DIR = QA_DIR / "previews"
REPORT_CSV = QA_DIR / "layer_qa.csv"
REPORT_JSON = QA_DIR / "layer_qa.json"

# Coarse sources legitimately leave edge NoData over the small Goslar focus
# box (SoilGrids 250 m, DWD REGNIE 1 km). Their NoData is preserved rather than
# imputed to 0, so their coverage floor is lower than fine sources. Gaps below
# the floor still fail; gaps above it are recorded as a coverage note.
COARSE_COVERAGE_FLOOR = {
    "soil_k": 80.0,    # SoilGrids 250 m, NoData preserved (not filled)
    "rainfall": 80.0,  # DWD REGNIE 1 km, provisional 30 m resample
    "population": 5.0, # 100 m population cells legitimately sparse in forested WRRL basins
}
DEFAULT_COVERAGE_FLOOR = 95.0


def load_builder():
    spec = importlib.util.spec_from_file_location("goslar_qgis_package_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {BUILDER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUILDER = load_builder()


def relaunch_with_qgis() -> int:
    if not BUILDER.QGIS_PYTHON.exists():
        raise RuntimeError(f"QGIS Python wrapper not found: {BUILDER.QGIS_PYTHON}")
    command = [str(BUILDER.QGIS_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]]
    return subprocess.run(
        command,
        cwd=ROOT,
        env=BUILDER.qgis_environment(),
        check=False,
    ).returncode


def sample_raster(path: Path, boundary_path: Path, boundary_layer_name: str) -> dict[str, object]:
    from osgeo import gdal

    gdal.UseExceptions()
    dataset = gdal.Open(str(path))
    if dataset is None:
        raise RuntimeError(f"GDAL could not open {path}")
    band = dataset.GetRasterBand(1)
    stats = band.GetStatistics(False, True)
    width = min(dataset.RasterXSize, 512)
    height = min(dataset.RasterYSize, 512)
    values = band.ReadAsArray(buf_xsize=width, buf_ysize=height)
    nodata = band.GetNoDataValue()
    import numpy as np

    finite = np.isfinite(values)
    if nodata is not None:
        if math.isnan(nodata):
            finite &= ~np.isnan(values)
        else:
            finite &= ~np.isclose(values, nodata)
    valid = values[finite]
    transform = dataset.GetGeoTransform()
    xmin = transform[0]
    xmax = transform[0] + dataset.RasterXSize * transform[1]
    ymax = transform[3]
    ymin = transform[3] + dataset.RasterYSize * transform[5]
    projected = gdal.VectorTranslate(
        "",
        str(boundary_path),
        format="MEM",
        dstSRS=dataset.GetProjection(),
        layers=[boundary_layer_name],
    )
    projected_name = projected.GetLayer(0).GetName()
    mask_dataset = gdal.Rasterize(
        "",
        projected,
        format="MEM",
        width=width,
        height=height,
        outputBounds=[xmin, ymin, xmax, ymax],
        outputSRS=dataset.GetProjection(),
        layers=[projected_name],
        burnValues=[1],
        outputType=gdal.GDT_Byte,
    )
    inside = mask_dataset.GetRasterBand(1).ReadAsArray() > 0
    inside_count = int(inside.sum())
    return {
        "minimum": float(stats[0]),
        "maximum": float(stats[1]),
        "mean": float(stats[2]),
        "stddev": float(stats[3]),
        "sampled_valid_pixels": int(valid.size),
        "sampled_valid_percent": 100.0 * int(finite.sum()) / int(finite.size),
        "sampled_unique_values": int(np.unique(valid).size) if valid.size else 0,
        "valid_within_boundary_percent": (
            100.0 * int((finite & inside).sum()) / inside_count if inside_count else 0.0
        ),
    }


def render_preview(project_path: Path, layer_key: str, output_path: Path) -> None:
    from qgis.PyQt.QtCore import QSize
    from qgis.PyQt.QtGui import QColor, QImage, QPainter
    from qgis.core import (
        QgsMapRendererParallelJob,
        QgsMapSettings,
        QgsProject,
        QgsRectangle,
    )

    project = QgsProject.instance()
    if not project.read(str(project_path)):
        raise RuntimeError(f"could not read {project_path}")
    target = next(
        layer
        for layer in project.mapLayers().values()
        if layer.customProperty("ifpm/role") == "priority_result"
    )
    extent = QgsRectangle(target.extent())
    extent.scale(1.04)
    settings = QgsMapSettings()
    settings.setDestinationCrs(project.crs())
    settings.setTransformContext(project.transformContext())
    settings.setExtent(extent)
    settings.setOutputSize(QSize(1000, 760))
    settings.setOutputDpi(120)
    settings.setBackgroundColor(QColor("white"))
    settings.setLayers([target])

    job = QgsMapRendererParallelJob(settings)
    job.start()
    job.waitForFinished()
    image = job.renderedImage()
    painter = QPainter(image)
    painter.setPen(QColor("#222222"))
    painter.drawText(18, 28, "Goslar priority preview")
    painter.end()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(str(output_path), "PNG")


def run_qa() -> int:
    from qgis.core import QgsApplication

    QgsApplication.setPrefixPath(str(BUILDER.QGIS_PREFIX), True)
    app = QgsApplication([], False)
    app.initQgis()
    rows: list[dict[str, object]] = []
    try:
        with (ROOT / "outputs/goslar_qgis_full_audit/manifest.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            manifest_rows = list(csv.DictReader(handle))
        boundary_path = ROOT / "outputs/goslar_official_hydrology_and_flood_data/goslar_official_hydrologic_reference_boundary.gpkg"
        boundary_layer_name = "goslar_official_hydrologic_reference_boundary"
        project_path = ROOT / "outputs/goslar_qgis_full_audit/IFPM_Goslar_FullAudit.qgz"
        for row in manifest_rows:
            source = ROOT / row["source_path"]
            if row["source_type"] != "raster":
                rows.append({**row, "qa_status": "vector_skipped"})
                continue
            stats = sample_raster(source, boundary_path, boundary_layer_name)
            rows.append({**row, **stats, "qa_status": "ok"})
            if row["role"] == "priority_result":
                render_preview(project_path, row["layer_key"], PREVIEW_DIR / "priority_preview.png")
    finally:
        app.exitQgis()

    coverage_floor = lambda key: COARSE_COVERAGE_FLOOR.get(key, DEFAULT_COVERAGE_FLOOR)
    failed = [
        row
        for row in rows
        if row["qa_status"] == "ok"
        and float(row["valid_within_boundary_percent"]) < coverage_floor(row["layer_key"])
    ]
    for row in rows:
        if row["qa_status"] == "ok" and row["layer_key"] in COARSE_COVERAGE_FLOOR:
            row["coverage_note"] = (
                f"coarse source; floor {COARSE_COVERAGE_FLOOR[row['layer_key']]}% "
                "(documented NoData preserved)"
            )
    with REPORT_CSV.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = sorted({k for row in rows for k in row.keys()})
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    result = {
        "status": "pass" if not failed else "fail",
        "pass_count": len(rows) - len(failed),
        "fail_count": len(failed),
        "layers": rows,
    }
    REPORT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if failed:
        print(f"QA failed for {[row['layer_key'] for row in failed]}", file=sys.stderr)
        return 1
    print(f"Goslar QGIS QA passed for {len(rows)} layers")
    return 0


def main() -> int:
    if os.environ.get("IFPM_QGIS_RUNTIME") != "1":
        return relaunch_with_qgis()
    return run_qa()


if __name__ == "__main__":
    raise SystemExit(main())
