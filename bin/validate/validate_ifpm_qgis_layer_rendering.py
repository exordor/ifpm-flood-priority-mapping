#!/usr/bin/env python3
"""Render and audit every governed raster in the IFPM QGIS projects."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = ROOT / "bin/package/build_ifpm_qgis_project_package.py"
QA_DIR = ROOT / "outputs/qgis_project_package/layer_qa"
PREVIEW_DIR = QA_DIR / "previews"
REPORT_CSV = QA_DIR / "layer_qa.csv"
REPORT_JSON = QA_DIR / "layer_qa.json"


def load_builder():
    spec = importlib.util.spec_from_file_location("ifpm_qgis_package_builder", BUILDER_PATH)
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


def _sample_raster(
    path: Path,
    boundary_path: Path | None = None,
    boundary_layer_name: str = "",
) -> dict[str, float | int | None]:
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
    sampled_pixels = int(values.size)
    valid_pixels = int(valid.size)
    unique_values = int(np.unique(valid).size) if valid_pixels else 0
    result = {
        "minimum": float(stats[0]),
        "maximum": float(stats[1]),
        "mean": float(stats[2]),
        "stddev": float(stats[3]),
        "nodata": None if nodata is None else float(nodata),
        "sampled_pixels": sampled_pixels,
        "sampled_valid_pixels": valid_pixels,
        "sampled_valid_percent": 100.0 * valid_pixels / sampled_pixels,
        "sampled_unique_values": unique_values,
        "sampled_boundary_pixels": None,
        "valid_within_boundary_percent": None,
    }
    if boundary_path is not None:
        transform = dataset.GetGeoTransform()
        xmin = transform[0]
        xmax = transform[0] + dataset.RasterXSize * transform[1]
        ymax = transform[3]
        ymin = transform[3] + dataset.RasterYSize * transform[5]
        projected_boundary = gdal.VectorTranslate(
            "",
            str(boundary_path),
            format="MEM",
            dstSRS=dataset.GetProjection(),
            layers=[boundary_layer_name],
        )
        if projected_boundary is None:
            raise RuntimeError(f"could not reproject boundary for {path}")
        projected_layer_name = projected_boundary.GetLayer(0).GetName()
        mask_dataset = gdal.Rasterize(
            "",
            projected_boundary,
            format="MEM",
            width=width,
            height=height,
            outputBounds=[xmin, ymin, xmax, ymax],
            outputSRS=dataset.GetProjection(),
            layers=[projected_layer_name],
            burnValues=[1],
            outputType=gdal.GDT_Byte,
        )
        if mask_dataset is None:
            raise RuntimeError(f"could not rasterize boundary for {path}")
        inside = mask_dataset.GetRasterBand(1).ReadAsArray() > 0
        inside_count = int(inside.sum())
        result["sampled_boundary_pixels"] = inside_count
        result["valid_within_boundary_percent"] = (
            100.0 * int((finite & inside).sum()) / inside_count if inside_count else 0.0
        )
        mask_dataset = None
        projected_boundary = None
    dataset = None
    return result


def _image_metrics(image) -> dict[str, float | int]:
    from qgis.PyQt.QtGui import QColor

    step = 4
    sampled = 0
    non_background = 0
    colors: set[int] = set()
    for y in range(0, image.height(), step):
        for x in range(0, image.width(), step):
            color = QColor(image.pixel(x, y))
            sampled += 1
            if color.red() < 246 or color.green() < 246 or color.blue() < 246:
                non_background += 1
                colors.add(color.rgb())
    return {
        "render_sampled_pixels": sampled,
        "render_non_background_percent": 100.0 * non_background / sampled,
        "render_unique_colors": len(colors),
    }


def _alpha_metrics(image) -> dict[str, float | int]:
    step = 2
    sampled = 0
    visible = 0
    for y in range(0, image.height(), step):
        for x in range(0, image.width(), step):
            sampled += 1
            if (image.pixel(x, y) >> 24) & 0xFF:
                visible += 1
    return {
        "target_render_sampled_pixels": sampled,
        "target_symbol_percent": 100.0 * visible / sampled,
    }


def _render_layers(
    project,
    layers,
    extent_layer,
    label: str,
    output_path: Path | None,
    *,
    transparent: bool = False,
    draw_label: bool = True,
) -> dict[str, float | int]:
    from qgis.PyQt.QtCore import QSize
    from qgis.PyQt.QtGui import QColor, QImage, QPainter
    from qgis.core import (
        QgsCoordinateTransform,
        QgsMapRendererParallelJob,
        QgsMapSettings,
        QgsRectangle,
    )

    extent = QgsRectangle(extent_layer.extent())
    if extent_layer.crs() != project.crs():
        transform = QgsCoordinateTransform(
            extent_layer.crs(), project.crs(), project.transformContext()
        )
        extent = transform.transformBoundingBox(extent)
    extent.scale(1.04)
    settings = QgsMapSettings()
    settings.setDestinationCrs(project.crs())
    settings.setTransformContext(project.transformContext())
    settings.setExtent(extent)
    settings.setOutputSize(QSize(1000, 760))
    settings.setOutputDpi(120)
    settings.setBackgroundColor(QColor(255, 255, 255, 0) if transparent else QColor("white"))
    settings.setLayers(layers)

    job = QgsMapRendererParallelJob(settings)
    job.start()
    job.waitForFinished()
    image = job.renderedImage()

    if draw_label:
        painter = QPainter(image)
        painter.setPen(QColor("#222222"))
        painter.drawText(18, 28, label)
        painter.end()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if not image.save(str(output_path), "PNG"):
            raise RuntimeError(f"could not save {output_path}")
    return _alpha_metrics(image) if transparent else _image_metrics(image)


def _style_item_count(layer) -> int:
    renderer = layer.renderer()
    shader = renderer.shader() if renderer is not None and hasattr(renderer, "shader") else None
    function = shader.rasterShaderFunction() if shader is not None else None
    return len(function.colorRampItemList()) if function is not None else 0


def _write_contact_sheet(site_key: str, rows: list[dict[str, object]]) -> Path:
    from qgis.PyQt.QtCore import QRect, Qt
    from qgis.PyQt.QtGui import QColor, QFont, QImage, QPainter

    columns = 4
    cell_width = 500
    cell_height = 410
    rows_count = math.ceil(len(rows) / columns)
    sheet = QImage(columns * cell_width, rows_count * cell_height, QImage.Format_RGB32)
    sheet.fill(QColor("white"))
    painter = QPainter(sheet)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    font = QFont()
    font.setPixelSize(17)
    painter.setFont(font)
    painter.setPen(QColor("#222222"))
    for index, row in enumerate(rows):
        column = index % columns
        row_index = index // columns
        x = column * cell_width
        y = row_index * cell_height
        source = QImage(str(ROOT / str(row["preview_path"])))
        target = QRect(x + 8, y + 8, cell_width - 16, cell_height - 44)
        thumbnail = source.scaled(
            target.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        painter.drawImage(
            x + (cell_width - thumbnail.width()) // 2,
            y + 8 + (target.height() - thumbnail.height()) // 2,
            thumbnail,
        )
        painter.drawText(x + 12, y + cell_height - 14, str(row["display_name"]))
    painter.end()
    path = QA_DIR / f"{site_key}_layer_contact_sheet.png"
    if not sheet.save(str(path), "PNG"):
        raise RuntimeError(f"could not save {path}")
    return path


def _audit_site(project, site_key: str, project_path: Path) -> list[dict[str, object]]:
    from qgis.core import QgsCoordinateTransform, QgsFeatureRequest, QgsGeometry

    site = BUILDER.SITE_SPECS[site_key]
    if not project.read(str(project_path)):
        raise RuntimeError(f"QGIS could not read {project_path}")
    layers = {
        spec.key: next(
            layer
            for layer in project.mapLayers().values()
            if layer.customProperty("ifpm/site") == site_key and layer.name() == spec.name
        )
        for spec in site.layers
    }
    boundary = next(
        (layers[spec.key] for spec in site.layers if spec.role == "boundary"),
        None,
    )
    priority = layers["priority"]
    boundary_spec = next(spec for spec in site.layers if spec.role == "boundary")
    boundary_source_parts = boundary.source().split("|", 1)
    boundary_path = Path(boundary_source_parts[0])
    boundary_layer_name = boundary_spec.layer_name
    if len(boundary_source_parts) == 2 and "layername=" in boundary_source_parts[1]:
        boundary_layer_name = boundary_source_parts[1].split("layername=", 1)[1].split("|", 1)[0]

    def boundary_geometry_for(layer):
        geometries = []
        transform = None
        if boundary.crs() != layer.crs():
            transform = QgsCoordinateTransform(
                boundary.crs(), layer.crs(), project.transformContext()
            )
        for feature in boundary.getFeatures():
            geometry = QgsGeometry(feature.geometry())
            if transform is not None:
                geometry.transform(transform)
            geometries.append(geometry)
        return QgsGeometry.unaryUnion(geometries)
    rows: list[dict[str, object]] = []
    for spec in site.layers:
        layer = layers[spec.key]
        source = Path(layer.source().split("|", 1)[0])
        preview = PREVIEW_DIR / site_key / f"{spec.key}.png"
        issues: list[str] = []
        layer_extent = layer.extent()
        if layer.crs() != priority.crs():
            transform = QgsCoordinateTransform(
                layer.crs(), priority.crs(), project.transformContext()
            )
            layer_extent = transform.transformBoundingBox(layer_extent)
        if not layer_extent.intersects(priority.extent()):
            issues.append("extent_does_not_intersect_priority")

        if spec.kind == "raster":
            raster_stats = _sample_raster(
                source,
                boundary_path if spec.role in {"priority_result", "criterion"} else None,
                boundary_layer_name,
            )
            rendered_layers = [layer]
            if boundary is not None:
                rendered_layers.insert(0, boundary)
            render_stats = _render_layers(
                project, rendered_layers, priority, spec.name, preview
            )
            feature_count: int | str = ""
            if raster_stats["sampled_valid_percent"] < 1:
                issues.append("near_empty_sampled_coverage")
            if raster_stats["sampled_unique_values"] < 2:
                issues.append("constant_or_empty_sample")
        else:
            raster_stats = {
                "minimum": "",
                "maximum": "",
                "mean": "",
                "stddev": "",
                "nodata": "",
                "sampled_pixels": "",
                "sampled_valid_pixels": "",
                "sampled_valid_percent": "",
                "sampled_unique_values": "",
                "sampled_boundary_pixels": "",
                "valid_within_boundary_percent": "",
            }
            feature_count = layer.featureCount()
            rendered_layers = [layer]
            if boundary is not None and layer != boundary:
                rendered_layers.append(boundary)
            if layer != priority:
                rendered_layers.append(priority)
            render_stats = _render_layers(
                project, rendered_layers, priority, spec.name, preview
            )
            filter_extent = priority.extent()
            if priority.crs() != layer.crs():
                transform = QgsCoordinateTransform(
                    priority.crs(), layer.crs(), project.transformContext()
                )
                filter_extent = transform.transformBoundingBox(filter_extent)
            priority_extent_feature_count = sum(
                1
                for _ in layer.getFeatures(
                    QgsFeatureRequest().setFilterRect(filter_extent)
                )
            )
            study_boundary_geometry = boundary_geometry_for(layer)
            within_boundary_feature_count = sum(
                1
                for feature in layer.getFeatures()
                if feature.hasGeometry()
                and feature.geometry().intersects(study_boundary_geometry)
            )
            render_stats.update(
                _render_layers(
                    project,
                    [layer],
                    priority,
                    spec.name,
                    None,
                    transparent=True,
                    draw_label=False,
                )
            )
            if feature_count < 1:
                issues.append("empty_vector_layer")
            if priority_extent_feature_count < 1:
                issues.append("no_vector_features_intersect_priority_extent")
            if within_boundary_feature_count < 1:
                issues.append("no_vector_features_intersect_study_boundary")
            if render_stats["target_symbol_percent"] <= 0:
                issues.append("vector_symbols_not_rendered")

        if spec.kind == "raster":
            priority_extent_feature_count: int | str = ""
            within_boundary_feature_count: int | str = ""
            render_stats.update(
                {"target_render_sampled_pixels": "", "target_symbol_percent": ""}
            )

        if render_stats["render_non_background_percent"] < 2:
            issues.append("near_blank_render")
        if render_stats["render_unique_colors"] < 3:
            issues.append("low_render_color_variation")
        if spec.kind == "raster" and BUILDER._is_normalized(spec):
            if raster_stats["minimum"] < -1e-5 or raster_stats["maximum"] > 1.00001:
                issues.append("normalized_range_outside_0_1")
        if spec.role in {"priority_result", "criterion"}:
            if float(raster_stats["valid_within_boundary_percent"] or 0) < 90:
                issues.append("low_valid_coverage_within_boundary")
        style_items: int | str = _style_item_count(layer) if spec.kind == "raster" else ""
        if spec.kind == "raster" and style_items != 5:
            issues.append("unexpected_style_class_count")

        rows.append(
            {
                "site": site_key,
                "layer_key": spec.key,
                "display_name": spec.name,
                "role": spec.role,
                "unit": spec.unit,
                "claim_level": spec.claim_level,
                "source_path": str(source),
                "provider_crs": layer.crs().authid(),
                "feature_count": feature_count,
                "priority_extent_feature_count": priority_extent_feature_count,
                "within_boundary_feature_count": within_boundary_feature_count,
                "style_class_count": style_items,
                "preview_path": str(preview.relative_to(ROOT)),
                **raster_stats,
                **render_stats,
                "issues": ";".join(issues),
                "qa_status": "review" if issues else "pass",
            }
        )
    return rows


def run() -> dict[str, object]:
    from qgis.core import QgsApplication, QgsProject

    QgsApplication.setPrefixPath(str(BUILDER.QGIS_PREFIX), True)
    app = QgsApplication([], False)
    app.initQgis()
    project = QgsProject.instance()
    QA_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    try:
        for site_key, site in BUILDER.SITE_SPECS.items():
            site_rows = _audit_site(
                project,
                site_key,
                BUILDER.PORTABLE_DIR / site.project_file,
            )
            rows.extend(site_rows)
            _write_contact_sheet(site_key, site_rows)
            project.clear()
    finally:
        project.clear()
        app.exitQgis()

    fields = list(rows[0])
    with REPORT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    result = {
        "status": "review_required" if any(row["issues"] for row in rows) else "pass",
        "validator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "builder_sha256": hashlib.sha256(BUILDER_PATH.read_bytes()).hexdigest(),
        "manifest_sha256": hashlib.sha256(BUILDER.MANIFEST.read_bytes()).hexdigest(),
        "portable_project_sha256": {
            site.project_file: hashlib.sha256(
                (BUILDER.PORTABLE_DIR / site.project_file).read_bytes()
            ).hexdigest()
            for site in BUILDER.SITE_SPECS.values()
        }
        | {
            "IFPM_Combined.qgz": hashlib.sha256(
                (BUILDER.PORTABLE_DIR / "IFPM_Combined.qgz").read_bytes()
            ).hexdigest()
        },
        "layer_count": len(rows),
        "pass_count": sum(not row["issues"] for row in rows),
        "review_count": sum(bool(row["issues"]) for row in rows),
        "issues": [
            {"site": row["site"], "layer_key": row["layer_key"], "issues": row["issues"]}
            for row in rows
            if row["issues"]
        ],
        "report_csv": str(REPORT_CSV.relative_to(ROOT)),
        "preview_directory": str(PREVIEW_DIR.relative_to(ROOT)),
        "contact_sheets": [
            str((QA_DIR / f"{site_key}_layer_contact_sheet.png").relative_to(ROOT))
            for site_key in BUILDER.SITE_SPECS
        ],
    }
    REPORT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    return argparse.ArgumentParser(description=__doc__).parse_args()


def main() -> int:
    parse_args()
    if os.environ.get("IFPM_QGIS_RUNTIME") != "1":
        return relaunch_with_qgis()
    result = run()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
