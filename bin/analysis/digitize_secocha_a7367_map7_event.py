#!/usr/bin/env python3
"""Georeference A7367 Map 7 and extract February 5 event polygons.

This is a reproducible, source-anchored semi-automatic digitization candidate.
It does not replace an official vector dataset or claim survey-grade accuracy.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from PIL import Image
from rasterio.features import geometry_mask, rasterize, shapes
from rasterio.transform import Affine
from scipy.ndimage import binary_closing, binary_fill_holes, label
from shapely.geometry import shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "data/validation/secocha_2023_validation/official_reports/ingemmet_a7367_secocha_hazard_assessment.pdf"
TMP = ROOT / "tmp/pdfs/secocha_a7367_map7"
OUT = ROOT / "outputs/secocha_2023_validation/observed_hazard"
PAGE = 75
RENDER_DPI = 300
RENDER = TMP / "a7367_page75_300dpi.png"
RENDER_MANIFEST = TMP / "render_manifest.json"
MAP_TIF = OUT / "a7367_map7_georeferenced_utm18s.tif"
GPKG = OUT / "secocha_2023_map7_event_digitization.gpkg"
MANIFEST = OUT / "digitization_manifest.json"
COMPARISON = OUT / "secocha_2023_event_pim_comparison.json"
FIGURE = OUT / "secocha_2023_event_footprint_comparison.png"
PIM = ROOT / "outputs/peru_secocha_a7367_reference_extent_v1/priority_scenarios/scenarios/priority_secocha_direct_pim.tif"
BOUNDARY = ROOT / "outputs/peru_secocha_boundary/peru_secocha_active_boundary.gpkg"
MINING = ROOT / "data/raw/ingemmet_catastro_minero_peru_secocha/secocha_pequena_mineria.gpkg"
PIM_RUN_MANIFEST = ROOT / "outputs/peru_secocha_a7367_reference_extent_v1/priority_scenarios/run_manifest.json"
BOUNDARY_ID = "peru_secocha_a7367_reference_extent_v1"
PIM_HIGH_THRESHOLD = 0.6
SEGMENTATION_RULE_VERSION = "map7_legend_colour_v1"
EVIDENCE_INPUTS = [
    ROOT / "outputs/secocha_2023_validation/ingemmet_field_anchors.geojson",
    ROOT / "outputs/secocha_2023_validation/indeci_response_locations.geojson",
]

# Pixel control points read from the printed UTM grid on PDF page 75.
# Pixel coordinates refer to the 300 dpi full-page render.
X_CONTROL = [(276, 692000), (750, 693000), (1224, 694000), (1698, 695000), (2172, 696000)]
Y_CONTROL = [(385, 8236000), (859, 8235000), (1333, 8234000),
             (1807, 8233000), (2281, 8232000), (2755, 8231000)]
CROP = (45, 45, 2395, 3030)  # left, top, right, bottom; map frame only


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_page() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    expected = {"source_pdf_sha256": sha256(PDF), "source_pdf_page": PAGE, "render_dpi": RENDER_DPI}
    if RENDER.exists() and RENDER_MANIFEST.exists():
        try:
            cached = json.loads(RENDER_MANIFEST.read_text(encoding="utf-8"))
            if all(cached.get(key) == value for key, value in expected.items()) and cached.get("render_sha256") == sha256(RENDER):
                return
        except (OSError, json.JSONDecodeError):
            pass
    if RENDER.exists():
        RENDER.unlink()
    prefix = RENDER.with_suffix("")
    subprocess.run(["pdftoppm", "-f", str(PAGE), "-l", str(PAGE), "-png", "-r", str(RENDER_DPI),
                    "-singlefile", str(PDF), str(prefix)], check=True)
    with Image.open(RENDER) as image:
        expected.update({"render_sha256": sha256(RENDER), "render_width_px": image.width, "render_height_px": image.height})
    RENDER_MANIFEST.write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")


def georeference() -> tuple[np.ndarray, Affine, dict]:
    image = np.asarray(Image.open(RENDER).convert("RGB"))
    left, top, right, bottom = CROP
    cropped = image[top:bottom, left:right]
    ax, cx = np.polyfit(*map(np.asarray, zip(*X_CONTROL)), 1)
    ay, cy = np.polyfit(*map(np.asarray, zip(*Y_CONTROL)), 1)
    # Affine is defined at pixel corners; fitted coordinates are pixel centres.
    transform = Affine(ax, 0, cx + ax * (left - 0.5), 0, ay, cy + ay * (top - 0.5))
    profile = {
        "driver": "GTiff", "height": cropped.shape[0], "width": cropped.shape[1],
        "count": 3, "dtype": "uint8", "crs": "EPSG:32718", "transform": transform,
        "compress": "deflate", "tiled": True, "blockxsize": 256, "blockysize": 256,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    with rasterio.open(MAP_TIF, "w", **profile) as dst:
        dst.write(np.moveaxis(cropped, 2, 0))
        dst.update_tags(
            SOURCE="INGEMMET Informe Tecnico A7367, Map 7, PDF page 75",
            GEOREFERENCE="Manual printed-grid control points; approximate, not survey grade",
        )
    meta = {
        "x_pixel_to_utm": {"scale_m_per_pixel": float(ax), "intercept": float(cx)},
        "y_pixel_to_utm": {"scale_m_per_pixel": float(ay), "intercept": float(cy)},
        "control_points_x": X_CONTROL, "control_points_y": Y_CONTROL,
        "estimated_registration_uncertainty_m": 10,
        "crop_full_page_pixels": list(CROP),
    }
    return cropped, transform, meta


def remove_small(mask: np.ndarray, minimum_pixels: int = 30) -> np.ndarray:
    labelled, count = label(mask)
    sizes = np.bincount(labelled.ravel())
    keep = sizes >= minimum_pixels
    keep[0] = False
    return keep[labelled]


def event_masks(rgb: np.ndarray) -> dict[str, np.ndarray]:
    values = rgb.astype("int16")
    red, green, blue = (values[:, :, index] for index in range(3))
    # Legend-derived colour rules. The PDF overlays are semi-transparent, so
    # channel relationships are more stable than one exact RGB triplet.
    huaico = (
        (red > 170) & (green > 125) & (blue > 195)
        & ((blue - red) > 8) & ((blue - green) > 30) & ((red - green) > 15)
    )
    mudflow = (
        (red > 170) & (blue > 140) & ((red - blue) > 8)
        & ((blue - green) > 35) & ((red - green) > 55)
    )
    cleaned = {}
    for name, mask in {"huaico_2023_02_05": huaico, "mudflow_2023_02_05": mudflow}.items():
        work = binary_closing(mask, iterations=2)
        work = remove_small(work, 30)
        work = binary_fill_holes(work)
        cleaned[name] = work.astype("uint8")
    return cleaned


def mask_geometry(mask: np.ndarray, transform: Affine):
    polygons = [shape(geom) for geom, value in shapes(mask, mask=mask.astype(bool), transform=transform) if value == 1]
    if not polygons:
        raise RuntimeError("event colour segmentation produced no polygons")
    return unary_union(polygons).buffer(0).simplify(2.0, preserve_topology=True)


def write_vectors(masks: dict[str, np.ndarray], transform: Affine) -> dict[str, object]:
    if GPKG.exists():
        GPKG.unlink()
    geoms = {}
    for layer_name, mask in masks.items():
        geom = mask_geometry(mask, transform)
        geoms[layer_name] = geom
        gpd.GeoDataFrame([{
            "event_date": "2023-02-05", "hazard_type": layer_name.split("_2023")[0],
            "source": "INGEMMET A7367 Map 7", "pdf_page": PAGE,
            "method": "legend-colour segmentation plus component cleanup",
            "confidence": "validation_candidate", "geometry": geom,
        }], crs="EPSG:32718").to_file(GPKG, layer=layer_name, driver="GPKG")
    combined = unary_union(list(geoms.values())).buffer(0)
    gpd.GeoDataFrame([{
        "event_date": "2023-02-05", "hazard_type": "combined_huaico_and_mudflow",
        "source": "INGEMMET A7367 Map 7", "pdf_page": PAGE,
        "method": "union of two explicit February 5 legend classes",
        "confidence": "validation_candidate", "geometry": combined,
    }], crs="EPSG:32718").to_file(GPKG, layer="event_footprint_candidate", driver="GPKG")
    return {**geoms, "event_footprint_candidate": combined}


def compare(geoms: dict[str, object]) -> dict[str, object]:
    event = geoms["event_footprint_candidate"]
    boundary = gpd.read_file(BOUNDARY, layer="secocha_active_boundary").geometry.iloc[0]
    with rasterio.open(PIM) as src:
        pim = src.read(1).astype("float32")
        valid = np.isfinite(pim) & (pim != src.nodata)
        event_grid = rasterize([(event, 1)], out_shape=pim.shape, transform=src.transform,
                               fill=0, dtype="uint8").astype(bool)
        cell_area_km2 = abs(src.transform.a * src.transform.e) / 1e6
        score_values = pim[event_grid & valid]
    high = valid & (pim >= PIM_HIGH_THRESHOLD)
    grid_event_valid = event_grid & valid
    mines = gpd.read_file(MINING).to_crs(32718)
    inside_event = mines.geometry.intersects(event)
    inside_boundary = mines.geometry.intersects(boundary)
    event_distances = mines.geometry.distance(event)
    event_cell_count = int(event_grid.sum())
    study_high_fraction = float(high.sum() / valid.sum())
    event_high_fraction = float((grid_event_valid & high).sum() / grid_event_valid.sum()) if grid_event_valid.any() else None
    event_mean = float(score_values.mean()) if score_values.size else None
    study_mean = float(pim[valid].mean())
    evidence_distance = {}
    evidence_lineage = []
    for name, path in [
        ("ingemmet_field_anchors", EVIDENCE_INPUTS[0]),
        ("indeci_response_locations", EVIDENCE_INPUTS[1]),
    ]:
        evidence = gpd.read_file(path).to_crs(32718)
        distances = evidence.geometry.distance(event)
        evidence_distance[name] = {
            "feature_count": int(len(evidence)),
            "intersecting_event_candidate": int((distances == 0).sum()),
            "within_250m": int((distances <= 250).sum()),
            "median_distance_m": float(np.median(distances)) if len(distances) else None,
        }
        evidence_lineage.append({"role": name, "path": str(path.relative_to(ROOT)), "sha256": sha256(path)})
    return {
        "boundary_id": BOUNDARY_ID,
        "boundary_path": str(BOUNDARY.relative_to(ROOT)),
        "boundary_sha256": sha256(BOUNDARY),
        "pim_raster": str(PIM.relative_to(ROOT)),
        "pim_raster_sha256": sha256(PIM),
        "pim_run_manifest": str(PIM_RUN_MANIFEST.relative_to(ROOT)),
        "pim_run_manifest_sha256": sha256(PIM_RUN_MANIFEST),
        "mining_path": str(MINING.relative_to(ROOT)),
        "mining_sha256": sha256(MINING),
        "source_pdf": str(PDF.relative_to(ROOT)),
        "source_pdf_sha256": sha256(PDF),
        "segmentation_rule_version": SEGMENTATION_RULE_VERSION,
        "pim_high_threshold": PIM_HIGH_THRESHOLD,
        "event_class_areas_km2": {name: float(geometry.area / 1e6) for name, geometry in geoms.items()},
        "event_geometry_area_km2": float(event.area / 1e6),
        "event_area_inside_active_boundary_km2": float(event.intersection(boundary).area / 1e6),
        "event_area_outside_active_boundary_km2": float(event.difference(boundary).area / 1e6),
        "event_grid_cells": event_cell_count,
        "event_cells_with_valid_pim": int(grid_event_valid.sum()),
        "event_pim_coverage_fraction": float(grid_event_valid.sum() / event_cell_count) if event_cell_count else None,
        "event_valid_pim_area_km2": float(grid_event_valid.sum() * cell_area_km2),
        "event_high_pim_cells": int((grid_event_valid & high).sum()),
        "event_high_pim_fraction": event_high_fraction,
        "study_area_high_pim_fraction": study_high_fraction,
        "high_pim_enrichment_ratio": float(event_high_fraction / study_high_fraction) if event_high_fraction is not None and study_high_fraction else None,
        "event_pim_mean": event_mean,
        "event_pim_median": float(np.median(score_values)) if score_values.size else None,
        "study_area_pim_mean": study_mean,
        "event_minus_study_pim_mean": float(event_mean - study_mean) if event_mean is not None else None,
        "mining_records_total": int(len(mines)),
        "mining_role": "external overlay only; excluded from PIM score",
        "mining_records_inside_active_boundary": int(inside_boundary.sum()),
        "mining_records_intersecting_event_candidate": int(inside_event.sum()),
        "mining_records_within_250m": int((event_distances <= 250).sum()),
        "mining_records_within_500m": int((event_distances <= 500).sum()),
        "mining_records_within_1000m": int((event_distances <= 1000).sum()),
        "mining_median_distance_to_event_m": float(np.median(event_distances)),
        "official_evidence_distance_checks": evidence_distance,
        "evidence_lineage": evidence_lineage,
        "claim_level": "validation_candidate",
        "interpretation": "Spatial agreement with semi-automatic report-map digitization; not accuracy/causality proof.",
    }


def plot_comparison(rgb: np.ndarray, transform: Affine, geoms: dict, report: dict) -> None:
    event = geoms["event_footprint_candidate"]
    extent = [transform.c, transform.c + transform.a * rgb.shape[1],
              transform.f + transform.e * rgb.shape[0], transform.f]
    fig, axes = plt.subplots(1, 2, figsize=(14, 7), facecolor="white")
    axes[0].imshow(rgb, extent=extent, origin="upper")
    for key, color, label_text in [("huaico_2023_02_05", "#00ffff", "5 Feb huaico candidate"),
                                   ("mudflow_2023_02_05", "#ffea00", "5 Feb mudflow candidate")]:
        gpd.GeoSeries([geoms[key]], crs=32718).boundary.plot(ax=axes[0], color=color, linewidth=.8, label=label_text)
    axes[0].set_title("A7367 Map 7 - extracted event classes", fontweight="bold")
    axes[0].legend(loc="lower left", fontsize=8)

    with rasterio.open(PIM) as src:
        pim = src.read(1).astype("float32"); pim[pim == src.nodata] = np.nan
        pextent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
    cmap = plt.get_cmap("YlOrRd").copy(); cmap.set_bad("#d9d9d9")
    image = axes[1].imshow(pim, extent=pextent, origin="upper", cmap=cmap, vmin=0, vmax=1)
    gpd.GeoSeries([event], crs=32718).boundary.plot(ax=axes[1], color="#00ffff", linewidth=1.1)
    mines = gpd.read_file(MINING).to_crs(32718)
    mines.plot(ax=axes[1], marker="^", color="#54278f", edgecolor="white", markersize=18, linewidth=.3)
    axes[1].set_xlim(pextent[0], pextent[1]); axes[1].set_ylim(pextent[2], pextent[3])
    axes[1].set_title("PIM with event candidate and mining overlay", fontweight="bold")
    fig.colorbar(image, ax=axes[1], fraction=.046, pad=.03, label="Relative priority index")
    for ax in axes:
        ax.set_xlabel("UTM 18S easting (m)"); ax.set_ylabel("northing (m)")
    fig.suptitle("Secocha 2023 historical-event validation - extended candidate",
                 x=.055, y=.985, ha="left", fontsize=16, fontweight="bold")
    fig.text(.055, .02,
             f"Candidate footprint: {report['event_geometry_area_km2']:.2f} km2; "
             f"PIM coverage of event cells: {report['event_pim_coverage_fraction']:.1%}; "
             f"High-PIM share on valid overlap: {report['event_high_pim_fraction']:.1%} "
             f"(study area: {report['study_area_high_pim_fraction']:.1%}). Gray cells are PIM NoData. "
             "Semi-automatic report-map extraction; requires analyst confirmation.",
             fontsize=9, color="#444444")
    fig.subplots_adjust(top=.90, bottom=.11, left=.06, right=.96, wspace=.20)
    fig.savefig(FIGURE, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    if not PDF.exists() or not PIM.exists():
        raise FileNotFoundError("required A7367 PDF or Secocha PIM is missing")
    render_page()
    rgb, transform, georef = georeference()
    masks = event_masks(rgb)
    geoms = write_vectors(masks, transform)
    report = compare(geoms)
    COMPARISON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    plot_comparison(rgb, transform, geoms, report)
    manifest = {
        "dataset_id": "secocha_2023_a7367_map7_event_digitization",
        "source_pdf": str(PDF.relative_to(ROOT)), "source_pdf_sha256": sha256(PDF),
        "source_pdf_page": PAGE, "map_number": 7, "map_crs": "EPSG:32718", "render_dpi": RENDER_DPI,
        "render_manifest": str(RENDER_MANIFEST.relative_to(ROOT)),
        "render_manifest_sha256": sha256(RENDER_MANIFEST), "render_sha256": sha256(RENDER),
        "boundary_id": BOUNDARY_ID, "boundary_path": str(BOUNDARY.relative_to(ROOT)), "boundary_sha256": sha256(BOUNDARY),
        "pim_raster": str(PIM.relative_to(ROOT)), "pim_raster_sha256": sha256(PIM),
        "pim_run_manifest": str(PIM_RUN_MANIFEST.relative_to(ROOT)), "pim_run_manifest_sha256": sha256(PIM_RUN_MANIFEST),
        "mining_path": str(MINING.relative_to(ROOT)), "mining_sha256": sha256(MINING),
        "segmentation_rule_version": SEGMENTATION_RULE_VERSION, "pim_high_threshold": PIM_HIGH_THRESHOLD,
        "mask_pixel_counts": {name: int(mask.sum()) for name, mask in masks.items()},
        "mask_areas_km2": {name: float(geometry.area / 1e6) for name, geometry in geoms.items()},
        "evidence_lineage": [{"path": str(path.relative_to(ROOT)), "sha256": sha256(path)} for path in EVIDENCE_INPUTS],
        "source_scale": "1:25,000", "georeferencing": georef,
        "extracted_classes": {
            "huaico_2023_02_05": "Huaico del 5 de febrero",
            "mudflow_2023_02_05": "Flujo de lodo del 5 de febrero",
        },
        "excluded_from_event_footprint": ["Caida de rocas", "Avalancha de detritos",
                                           "Flujo de detritos (huaico)", "Erosion de laderas (carcavas)"],
        "outputs": [
            {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
            for path in (MAP_TIF, GPKG, COMPARISON, FIGURE)
        ],
        "claim_level": "validation_candidate",
        "limitations": [
            "Semi-automatic colour segmentation of a rendered PDF map, not an official vector release.",
            "Approximate manual printed-grid georeferencing; estimated registration uncertainty is 10 m.",
            "Cartographic labels and anti-aliasing can create local omission or commission errors.",
            "Analyst visual confirmation is required before treating polygons as an observed event footprint.",
        ],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(MANIFEST.relative_to(ROOT)), **report}, indent=2))


if __name__ == "__main__":
    main()
