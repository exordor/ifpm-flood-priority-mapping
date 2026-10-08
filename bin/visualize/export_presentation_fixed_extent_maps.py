#!/usr/bin/env python3
"""Export presentation map panels with fixed, auditable geographic extents.

All panels for one case study share the same CRS, bounds, raster dimensions,
and borderless canvas. Legends and explanatory labels remain in PowerPoint.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/presentation_assets"

GOSLAR_BASE = ROOT / "outputs/srtm_1arcsec_goslar/priority_scenarios"
GOSLAR_INPUTS = {
    "goslar_pim_fixed_extent.png": GOSLAR_BASE / "scenarios/priority_goslar_direct_pim.tif",
    "goslar_flood_hazard_fixed_extent.png": GOSLAR_BASE / "pim_criteria/flood_hazard_0_1.tif",
    "goslar_sediment_fixed_extent.png": GOSLAR_BASE / "pim_criteria/sediment_0_1.tif",
    "goslar_landuse_fixed_extent.png": GOSLAR_BASE / "pim_criteria/landuse_asm_0_1.tif",
    "goslar_socioeconomic_fixed_extent.png": GOSLAR_BASE / "pim_criteria/socioeconomic_0_1.tif",
    "goslar_environmental_fixed_extent.png": GOSLAR_BASE / "pim_criteria/environmental_0_1.tif",
}
GOSLAR_HILLSHADE = ROOT / "outputs/presentation_assets/goslar_focus_area_hillshade.tif"
GOSLAR_HWRM = ROOT / "outputs/goslar_official_hydrology_and_flood_data/goslar_hwrm_flood_hazard_boundaries_12km.gpkg"
GOSLAR_HWRM_LAYER = "goslar_hwrm_flood_hazard_boundaries_12km"
GOSLAR_MINING = ROOT / "outputs/goslar_mining_context_overlay/goslar_mining_context_overlay.gpkg"
GOSLAR_ORIGINAL_FOCUS = ROOT / "outputs/goslar_focus_boundary/goslar_focus_boundary.gpkg"

SECOCHA_BASE = ROOT / "outputs/peru_secocha_a7367_reference_extent_v1/priority_scenarios"
SECOCHA_PIM = SECOCHA_BASE / "scenarios/priority_secocha_direct_pim.tif"
SECOCHA_INPUTS = {
    "secocha_pim_fixed_extent.png": SECOCHA_PIM,
    "secocha_flood_hazard_fixed_extent.png": SECOCHA_BASE / "pim_criteria/flood_hazard_0_1.tif",
    "secocha_sediment_fixed_extent.png": SECOCHA_BASE / "pim_criteria/sediment_0_1.tif",
    "secocha_landuse_fixed_extent.png": SECOCHA_BASE / "pim_criteria/landuse_asm_0_1.tif",
    "secocha_socioeconomic_fixed_extent.png": SECOCHA_BASE / "pim_criteria/socioeconomic_0_1.tif",
    "secocha_environmental_fixed_extent.png": SECOCHA_BASE / "pim_criteria/environmental_0_1.tif",
}
SECOCHA_MAP7 = ROOT / "outputs/secocha_2023_validation/observed_hazard/a7367_map7_georeferenced_utm18s.tif"
SECOCHA_EVENTS = ROOT / "outputs/secocha_2023_validation/observed_hazard/secocha_2023_map7_event_digitization.gpkg"
SECOCHA_HILLSHADE = ROOT / "outputs/presentation_assets/secocha_focus_area_hillshade.tif"
SECOCHA_MINING_OFFICIAL = ROOT / "outputs/secocha_official_proxy_replacements/secocha_official_exposure_mining.gpkg"
SECOCHA_MINING_POINTS = ROOT / "data/raw/ingemmet_catastro_minero_peru_secocha/secocha_pequena_mineria.gpkg"

PALETTES = {
    "goslar_pim_fixed_extent.png": ["#ffffcc", "#ffeda0", "#feb24c", "#f03b20", "#bd0026"],
    "goslar_flood_hazard_fixed_extent.png": ["#f7fbff", "#deebf7", "#9ecae1", "#3182bd", "#08519c"],
    "goslar_sediment_fixed_extent.png": ["#fff7ec", "#fee8c8", "#fdbb84", "#e34a33", "#7f0000"],
    "goslar_landuse_fixed_extent.png": ["#f7fcf5", "#c7e9c0", "#74c476", "#238b45", "#00441b"],
    "goslar_socioeconomic_fixed_extent.png": ["#ffffe5", "#fff7bc", "#fec44f", "#fe9929", "#cc4c02"],
    "goslar_environmental_fixed_extent.png": ["#f7f4f9", "#e7e1ef", "#c994c7", "#dd1c77", "#980043"],
    "secocha_pim_fixed_extent.png": ["#ffffcc", "#ffeda0", "#feb24c", "#f03b20", "#bd0026"],
    "secocha_flood_hazard_fixed_extent.png": ["#f7fbff", "#deebf7", "#9ecae1", "#3182bd", "#08519c"],
    "secocha_sediment_fixed_extent.png": ["#fff7ec", "#fee8c8", "#fdbb84", "#e34a33", "#7f0000"],
    "secocha_landuse_fixed_extent.png": ["#f7fcf5", "#c7e9c0", "#74c476", "#238b45", "#00441b"],
    "secocha_socioeconomic_fixed_extent.png": ["#ffffe5", "#fff7bc", "#fec44f", "#fe9929", "#cc4c02"],
    "secocha_environmental_fixed_extent.png": ["#f7f4f9", "#e7e1ef", "#c994c7", "#dd1c77", "#980043"],
    "secocha_pim_event_fixed_extent.png": ["#ffffcc", "#ffeda0", "#feb24c", "#f03b20", "#bd0026"],
}
BOUNDS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.000001]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_float(path: Path) -> tuple[np.ndarray, rasterio.coords.BoundingBox, str]:
    with rasterio.open(path) as src:
        array = src.read(1).astype("float32")
        if src.nodata is not None:
            array[array == src.nodata] = np.nan
        return array, src.bounds, src.crs.to_string()


def classes(array: np.ndarray) -> np.ma.MaskedArray:
    result = np.zeros(array.shape, dtype="uint8")
    valid = np.isfinite(array)
    for index, (low, high) in enumerate(zip(BOUNDS[:-1], BOUNDS[1:]), 1):
        result[valid & (array >= low) & (array < high)] = index
    result[valid & (array >= 1.0)] = 5
    return np.ma.masked_where(result == 0, result)


def fixed_canvas(width_px: int, height_px: int, dpi: int = 200):
    figure = plt.figure(figsize=(width_px / dpi, height_px / dpi), dpi=dpi, facecolor="white", frameon=False)
    axes = figure.add_axes([0, 0, 1, 1])
    axes.set_axis_off()
    return figure, axes


def render_score(
    array: np.ndarray,
    bounds: rasterio.coords.BoundingBox,
    colors: list[str],
    output: Path,
    width_px: int,
    height_px: int,
    overlays: list[tuple[gpd.GeoDataFrame, str, float]] | None = None,
    background: np.ndarray | None = None,
    original_focus: gpd.GeoDataFrame | None = None,
) -> None:
    figure, axes = fixed_canvas(width_px, height_px)
    cmap = ListedColormap(colors)
    cmap.set_bad("white", alpha=0)
    norm = BoundaryNorm(np.arange(0.5, 6.5), 5)
    extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]
    if background is not None:
        axes.imshow(background, cmap="gray", vmin=0, vmax=255, extent=extent,
                    origin="upper", interpolation="bilinear")
    axes.imshow(classes(array), cmap=cmap, norm=norm, extent=extent, origin="upper", interpolation="nearest")
    if overlays:
        for layer, color, linewidth in overlays:
            layer.boundary.plot(ax=axes, color=color, linewidth=linewidth, zorder=5)
    if original_focus is not None and not original_focus.empty:
        original_focus.boundary.plot(ax=axes, color="#FFFFFF", linewidth=3.6, zorder=6)
        original_focus.boundary.plot(ax=axes, color="#111111", linewidth=1.7, zorder=7)
    axes.set_xlim(bounds.left, bounds.right)
    axes.set_ylim(bounds.bottom, bounds.top)
    axes.set_aspect("equal", adjustable="box")
    figure.savefig(output, dpi=200, facecolor="white", transparent=False)
    plt.close(figure)


def hillshade_on_target(
    source_path: Path,
    target_bounds: rasterio.coords.BoundingBox,
    target_crs: str,
    width_px: int,
    height_px: int,
) -> np.ndarray:
    destination = np.full((height_px, width_px), 255, dtype="uint8")
    dst_transform = from_bounds(*target_bounds, width_px, height_px)
    with rasterio.open(source_path) as source:
        reproject(
            source=rasterio.band(source, 1),
            destination=destination,
            src_transform=source.transform,
            src_crs=source.crs,
            dst_transform=dst_transform,
            dst_crs=target_crs,
            src_nodata=source.nodata,
            dst_nodata=255,
            resampling=Resampling.bilinear,
            init_dest_nodata=True,
        )
    return destination


def render_hillshade(
    hillshade: np.ndarray,
    bounds: rasterio.coords.BoundingBox,
    output: Path,
    overlays: list[tuple[gpd.GeoDataFrame, str, float]],
    original_focus: gpd.GeoDataFrame | None = None,
) -> None:
    height_px, width_px = hillshade.shape
    figure, axes = fixed_canvas(width_px, height_px)
    extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]
    axes.imshow(hillshade, cmap="gray", vmin=0, vmax=255, extent=extent, origin="upper", interpolation="bilinear")
    for layer, color, linewidth in overlays:
        layer.boundary.plot(ax=axes, color=color, linewidth=linewidth, zorder=5)
    if original_focus is not None and not original_focus.empty:
        original_focus.boundary.plot(ax=axes, color="#FFFFFF", linewidth=3.6, zorder=6)
        original_focus.boundary.plot(ax=axes, color="#111111", linewidth=1.7, zorder=7)
    axes.set_xlim(bounds.left, bounds.right)
    axes.set_ylim(bounds.bottom, bounds.top)
    axes.set_aspect("equal", adjustable="box")
    figure.savefig(output, dpi=200, facecolor="white", transparent=False)
    plt.close(figure)


def render_mining_score(
    array: np.ndarray,
    bounds: rasterio.coords.BoundingBox,
    output: Path,
    width_px: int,
    height_px: int,
    rights: gpd.GeoDataFrame,
    points: gpd.GeoDataFrame,
    areas: gpd.GeoDataFrame | None = None,
    original_focus: gpd.GeoDataFrame | None = None,
) -> None:
    """Render PIM with mining rights, mapped areas, and location records."""
    figure, axes = fixed_canvas(width_px, height_px)
    cmap = ListedColormap(PALETTES["goslar_pim_fixed_extent.png"])
    cmap.set_bad("white", alpha=0)
    norm = BoundaryNorm(np.arange(0.5, 6.5), 5)
    extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]
    axes.imshow(classes(array), cmap=cmap, norm=norm, extent=extent,
                origin="upper", interpolation="nearest")
    if areas is not None and not areas.empty:
        areas.plot(ax=axes, facecolor="#C15ACD", edgecolor="#5B1A6E",
                   alpha=0.30, linewidth=0.9, zorder=5)
    if not rights.empty:
        rights.boundary.plot(ax=axes, color="#6A1B9A", linewidth=0.8, alpha=0.58, zorder=6)
    if not points.empty:
        points.plot(ax=axes, color="#2B0A3D", marker="^", markersize=28,
                    edgecolor="white", linewidth=0.55, zorder=7)
    if original_focus is not None and not original_focus.empty:
        original_focus.boundary.plot(ax=axes, color="#FFFFFF", linewidth=3.6, zorder=8)
        original_focus.boundary.plot(ax=axes, color="#111111", linewidth=1.7, zorder=9)
    axes.set_xlim(bounds.left, bounds.right)
    axes.set_ylim(bounds.bottom, bounds.top)
    axes.set_aspect("equal", adjustable="box")
    figure.savefig(output, dpi=200, facecolor="white", transparent=False)
    plt.close(figure)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "artifact_id": "presentation_fixed_extent_maps_20260818",
        "generated_date": str(date.today()),
        "status": "presentation export from current project outputs",
        "cases": {},
    }

    goslar_reference = GOSLAR_INPUTS["goslar_pim_fixed_extent.png"]
    with rasterio.open(goslar_reference) as reference:
        goslar_bounds = reference.bounds
        goslar_crs = reference.crs.to_string()
        goslar_width = reference.width * 2
        goslar_height = reference.height * 2
    goslar_original_focus = gpd.read_file(GOSLAR_ORIGINAL_FOCUS)
    if goslar_original_focus.crs is None:
        goslar_original_focus = goslar_original_focus.set_crs("EPSG:4326")
    goslar_original_focus = goslar_original_focus.to_crs(goslar_crs)
    goslar_outputs = []
    for filename, source in GOSLAR_INPUTS.items():
        array, bounds, crs = read_float(source)
        if crs != goslar_crs or bounds != goslar_bounds or array.shape != (goslar_height // 2, goslar_width // 2):
            raise RuntimeError(f"Goslar grid mismatch: {source}")
        output = OUT / filename
        render_score(
            array,
            bounds,
            PALETTES[filename],
            output,
            goslar_width,
            goslar_height,
            original_focus=goslar_original_focus if filename == "goslar_pim_fixed_extent.png" else None,
        )
        goslar_outputs.append({"path": str(output.relative_to(ROOT)), "sha256": sha256(output)})
    hwrm = gpd.read_file(GOSLAR_HWRM, layer=GOSLAR_HWRM_LAYER).to_crs(goslar_crs)
    hwrm = hwrm.cx[goslar_bounds.left:goslar_bounds.right, goslar_bounds.bottom:goslar_bounds.top]
    hwrm_overlays = [(hwrm, "#6A1B9A", 2.2)]
    goslar_context_output = OUT / "goslar_hwrm_context_fixed_extent.png"
    goslar_hillshade = hillshade_on_target(
        GOSLAR_HILLSHADE, goslar_bounds, goslar_crs, goslar_width, goslar_height
    )
    goslar_pim_array, _, _ = read_float(goslar_reference)
    render_hillshade(
        goslar_hillshade, goslar_bounds, goslar_context_output, hwrm_overlays,
        original_focus=goslar_original_focus,
    )
    goslar_pim_hwrm_output = OUT / "goslar_pim_hwrm_fixed_extent.png"
    render_score(
        goslar_pim_array,
        goslar_bounds,
        PALETTES["goslar_pim_fixed_extent.png"],
        goslar_pim_hwrm_output,
        goslar_width,
        goslar_height,
        hwrm_overlays,
        goslar_hillshade,
        original_focus=goslar_original_focus,
    )
    goslar_outputs.extend(
        {"path": str(item.relative_to(ROOT)), "sha256": sha256(item)}
        for item in [goslar_context_output, goslar_pim_hwrm_output]
    )
    goslar_rights = gpd.read_file(GOSLAR_MINING, layer="lbeg_mining_rights").to_crs(goslar_crs)
    goslar_points = gpd.read_file(GOSLAR_MINING, layer="osm_mining_points").to_crs(goslar_crs)
    goslar_areas = gpd.read_file(GOSLAR_MINING, layer="osm_mining_areas").to_crs(goslar_crs)
    goslar_rights = goslar_rights.cx[goslar_bounds.left:goslar_bounds.right, goslar_bounds.bottom:goslar_bounds.top]
    goslar_points = goslar_points.cx[goslar_bounds.left:goslar_bounds.right, goslar_bounds.bottom:goslar_bounds.top]
    goslar_areas = goslar_areas.cx[goslar_bounds.left:goslar_bounds.right, goslar_bounds.bottom:goslar_bounds.top]
    goslar_mining_output = OUT / "goslar_pim_mining_fixed_extent.png"
    render_mining_score(
        goslar_pim_array, goslar_bounds, goslar_mining_output, goslar_width, goslar_height,
        goslar_rights, goslar_points, goslar_areas,
        original_focus=goslar_original_focus,
    )
    goslar_outputs.append({"path": str(goslar_mining_output.relative_to(ROOT)), "sha256": sha256(goslar_mining_output)})
    manifest["cases"]["goslar"] = {
        "crs": goslar_crs,
        "bounds": list(goslar_bounds),
        "map_canvas_px": [goslar_width, goslar_height],
        "source_grid": [goslar_width // 2, goslar_height // 2],
        "mining_overlay_counts": {
            "rights": len(goslar_rights), "points": len(goslar_points), "areas": len(goslar_areas)
        },
        "original_focus_area_km2": float(goslar_original_focus.union_all().area / 1_000_000),
        "original_focus_source": str(GOSLAR_ORIGINAL_FOCUS.relative_to(ROOT)),
        "outputs": goslar_outputs,
    }

    secocha_array, secocha_bounds, secocha_crs = read_float(SECOCHA_PIM)
    secocha_width = secocha_array.shape[1] * 6
    secocha_height = secocha_array.shape[0] * 6
    huaico = gpd.read_file(SECOCHA_EVENTS, layer="huaico_2023_02_05").to_crs(secocha_crs)
    mudflow = gpd.read_file(SECOCHA_EVENTS, layer="mudflow_2023_02_05").to_crs(secocha_crs)
    event_overlays = [(huaico, "#00E6F0", 2.4), (mudflow, "#FFE600", 2.4)]

    secocha_criteria_outputs = []
    for filename, source in SECOCHA_INPUTS.items():
        array, bounds, crs = read_float(source)
        if crs != secocha_crs or bounds != secocha_bounds or array.shape != secocha_array.shape:
            raise RuntimeError(f"Secocha grid mismatch: {source}")
        output = OUT / filename
        render_score(array, bounds, PALETTES[filename], output, secocha_width, secocha_height)
        secocha_criteria_outputs.append(output)
    secocha_pim_output = OUT / "secocha_pim_fixed_extent.png"
    secocha_event_output = OUT / "secocha_event_candidates_fixed_extent.png"
    hillshade = hillshade_on_target(
        SECOCHA_HILLSHADE, secocha_bounds, secocha_crs, secocha_width, secocha_height
    )
    render_hillshade(hillshade, secocha_bounds, secocha_event_output, event_overlays)
    secocha_pim_event_output = OUT / "secocha_pim_event_fixed_extent.png"
    render_score(secocha_array, secocha_bounds, PALETTES[secocha_pim_event_output.name],
                 secocha_pim_event_output, secocha_width, secocha_height, event_overlays)

    secocha_rights = gpd.read_file(SECOCHA_MINING_OFFICIAL, layer="ingemmet_mining_rights").to_crs(secocha_crs)
    secocha_points = gpd.read_file(SECOCHA_MINING_POINTS, layer="pequena_mineria").to_crs(secocha_crs)
    secocha_rights = secocha_rights.cx[secocha_bounds.left:secocha_bounds.right, secocha_bounds.bottom:secocha_bounds.top]
    secocha_points = secocha_points.cx[secocha_bounds.left:secocha_bounds.right, secocha_bounds.bottom:secocha_bounds.top]
    secocha_mining_output = OUT / "secocha_pim_mining_fixed_extent.png"
    render_mining_score(
        secocha_array, secocha_bounds, secocha_mining_output, secocha_width, secocha_height,
        secocha_rights, secocha_points,
    )

    secocha_outputs = [*secocha_criteria_outputs, secocha_event_output, secocha_pim_event_output, secocha_mining_output]
    with rasterio.open(SECOCHA_MAP7) as map7_source:
        map7_source_bounds = list(map7_source.bounds)
    with rasterio.open(SECOCHA_HILLSHADE) as hillshade_source:
        hillshade_source_bounds = list(hillshade_source.bounds)
    manifest["cases"]["secocha"] = {
        "crs": secocha_crs,
        "bounds": list(secocha_bounds),
        "map_canvas_px": [secocha_width, secocha_height],
        "source_grid": [secocha_array.shape[1], secocha_array.shape[0]],
        "map7_source_bounds": map7_source_bounds,
        "hillshade_source_bounds": hillshade_source_bounds,
        "event_layers": ["huaico_2023_02_05", "mudflow_2023_02_05"],
        "mining_overlay_counts": {"rights": len(secocha_rights), "points": len(secocha_points)},
        "outputs": [{"path": str(item.relative_to(ROOT)), "sha256": sha256(item)} for item in secocha_outputs],
    }
    manifest["input_lineage"] = {
        str(path.relative_to(ROOT)): sha256(path)
        for path in [
            *GOSLAR_INPUTS.values(),
            GOSLAR_HILLSHADE,
            GOSLAR_HWRM,
            GOSLAR_MINING,
            GOSLAR_ORIGINAL_FOCUS,
            *SECOCHA_INPUTS.values(),
            SECOCHA_MAP7,
            SECOCHA_EVENTS,
            SECOCHA_HILLSHADE,
            SECOCHA_MINING_OFFICIAL,
            SECOCHA_MINING_POINTS,
        ]
    }
    manifest_path = OUT / "case_map_fixed_extent_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
