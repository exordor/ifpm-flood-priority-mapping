#!/usr/bin/env python3
"""Export Peru evidence overlays for the governed reporting figure chain.

Mining is an external post-PIM overlay and does not affect the current score.
Population remains part of socioeconomic exposure. SINPAD reference points are
shown only as a co-location diagnostic and are not independent model validation.
"""

from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from rasterio.enums import Resampling
from rasterio.transform import array_bounds
from rasterio.warp import calculate_default_transform, reproject


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bin/visualize"))

import export_paper_style_single_maps as maps


PIM = ROOT / (
    "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/"
    "priority_mentor_peru_direct_pim.tif"
)
EVIDENCE_SUPPORT = ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/evidence_support_class.tif"
POPULATION_EXPOSURE = ROOT / (
    "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/"
    "population_exposure_0_1.tif"
)
MINING = ROOT / "data/raw/ingemmet_catastro_minero_peru_pilot/peru_hybas_l7_6070641200_pequena_mineria.gpkg"
SINPAD = ROOT / "outputs/peru_gap_closure_analysis/peru_hybas_l7_6070641200_sinpad_pim_colocation.gpkg"
BOUNDARY = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
OUT_DIR = ROOT / "outputs/slide_ready_figures/peru_evidence_overlays"

INPUTS = [
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/priority_mentor_peru_direct_pim.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/evidence_support_class.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/population_exposure_0_1.tif",
    ROOT / "data/raw/ingemmet_catastro_minero_peru_pilot/peru_hybas_l7_6070641200_pequena_mineria.gpkg",
    ROOT / "outputs/peru_gap_closure_analysis/peru_hybas_l7_6070641200_sinpad_pim_colocation.gpkg",
    ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
]
OUTPUTS = [
    ROOT / "outputs/slide_ready_figures/peru_evidence_overlays/peru_priority_mining_population_overlay_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_evidence_overlays/peru_priority_mining_population_overlay_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_evidence_overlays/peru_sinpad_colocation_diagnostic_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_evidence_overlays/peru_sinpad_colocation_diagnostic_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_evidence_overlays/index.csv",
]

SINPAD_CLAIM_LEVEL = "diagnostic_only"
SINPAD_NOTE = (
    "SINPAD event reference points are shown as a co-location diagnostic, "
    "with unscored evidence gaps exposed; not independent model validation."
)

SITE = maps.Site(
    slug="peru",
    label="Peru Arequipa Region, mainly Vitor-La Joya-Santa Rita de Siguas west of Arequipa city",
    claim_level="diagnostic_only",
    priority_mean=PIM,
    flood_conditioning=ROOT / (
        "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/"
        "flood_conditioning_factors_0_1.tif"
    ),
    boundary_gpkg=BOUNDARY,
    boundary_layer="peru_pilot_boundary",
)


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_inputs() -> None:
    missing = [path for path in (PIM, EVIDENCE_SUPPORT, POPULATION_EXPOSURE, MINING, SINPAD, BOUNDARY) if not path.exists()]
    if missing:
        raise FileNotFoundError("missing overlay inputs: " + ", ".join(str(path) for path in missing))


def reproject_float(data: np.ndarray, profile: dict) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    bounds = array_bounds(profile["height"], profile["width"], profile["transform"])
    dst_transform, dst_width, dst_height = calculate_default_transform(
        profile["crs"],
        maps.DST_CRS,
        profile["width"],
        profile["height"],
        *bounds,
    )
    source = np.where(np.isfinite(data), data, -9999.0).astype("float32")
    destination = np.full((dst_height, dst_width), np.nan, dtype="float32")
    reproject(
        source=source,
        destination=destination,
        src_transform=profile["transform"],
        src_crs=profile["crs"],
        src_nodata=-9999.0,
        dst_transform=dst_transform,
        dst_crs=maps.DST_CRS,
        dst_nodata=np.nan,
        resampling=Resampling.bilinear,
    )
    west, south, east, north = array_bounds(dst_height, dst_width, dst_transform)
    return destination, (west, east, south, north)


def priority_base(ax) -> tuple[tuple[float, float, float, float], tuple[float, float, float, float]]:
    priority, profile = maps.read_raster(PIM)
    classes = maps.classify_equal_interval(priority, maps.PRIORITY_BOUNDS)
    projected, extent = maps.reproject_class(classes, profile)
    frame_extent = maps.frame_extent_for_legend(extent)
    masked = np.ma.masked_where(projected == 0, projected)
    cmap = ListedColormap(maps.PRIORITY_COLORS)
    norm = BoundaryNorm(np.arange(0.5, len(maps.PRIORITY_COLORS) + 1.5), len(maps.PRIORITY_COLORS))
    ax.imshow(masked, extent=extent, origin="upper", cmap=cmap, norm=norm, interpolation="nearest", zorder=1)
    evidence_support, evidence_profile = maps.read_raster(EVIDENCE_SUPPORT)
    if evidence_profile != profile:
        raise ValueError("evidence-support raster does not match the PIM grid")
    support = np.nan_to_num(evidence_support, nan=0).astype("uint8")
    support_projected, support_extent = maps.reproject_class(support, profile)
    if support_extent != extent:
        raise ValueError("evidence-support overlay extent mismatch")
    for support_value, hatch in ((2, "////"), (3, "xxxx"), (4, "....")):
        overlay = np.ma.masked_where(support_projected != support_value, support_projected)
        ax.contourf(
            overlay,
            levels=[support_value - 0.5, support_value + 0.5],
            colors="none",
            hatches=[hatch],
            extent=extent,
            origin="upper",
            zorder=3,
        )
    maps.add_boundary_and_frame(ax, SITE, frame_extent)
    maps.add_north_arrow(ax)
    maps.add_scale_bar(ax, frame_extent)
    return extent, frame_extent


def priority_handles() -> list[Patch]:
    handles = [
        Patch(facecolor=color, edgecolor="0.4", label=label)
        for label, color in zip(maps.PRIORITY_LABELS, maps.PRIORITY_COLORS, strict=True)
    ]
    handles.extend(
        [
            Patch(facecolor="none", edgecolor="#555555", hatch="////", label="Unscored: LS unavailable"),
            Patch(facecolor="none", edgecolor="#555555", hatch="xxxx", label="Unscored: K unavailable"),
            Patch(facecolor="none", edgecolor="#555555", hatch="....", label="Unscored: other evidence"),
        ]
    )
    return handles


def collapse_mining_locations(mining: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Return one feature per mapped coordinate while retaining source rows."""
    locations = mining.copy()
    locations["_location_key"] = locations.geometry.apply(lambda geometry: geometry.wkb_hex)
    return locations.drop_duplicates(subset="_location_key").copy()


def split_locations_by_boundary(
    locations: gpd.GeoDataFrame, boundary_geometry
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    inside_mask = locations.geometry.intersects(boundary_geometry)
    return locations[inside_mask].copy(), locations[~inside_mask].copy()


def collapse_sinpad_locations(events: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Return one feature per coordinate and preserve any flood-specific flag."""
    flood_by_location = events.groupby("coordinate_key")["is_flood_specific"].agg(
        lambda values: bool(values.astype(bool).any())
    )
    locations = events.drop_duplicates(subset="coordinate_key").copy()
    locations["is_flood_specific"] = locations["coordinate_key"].map(flood_by_location).astype(bool)
    return locations


def save(fig, stem: str) -> tuple[Path, Path]:
    png = OUT_DIR / f"{stem}_no_title_caption.png"
    pdf = png.with_suffix(".pdf")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    return png, pdf


def draw_population_contours(ax) -> list[float]:
    population, profile = maps.read_raster(POPULATION_EXPOSURE)
    projected, extent = reproject_float(population, profile)
    x = np.linspace(extent[0], extent[1], projected.shape[1])
    y = np.linspace(extent[3], extent[2], projected.shape[0])
    finite = projected[np.isfinite(projected)]
    levels = [float(value) for value in (0.20, 0.60) if finite.min() < value < finite.max()]
    if levels:
        ax.contour(
            x,
            y,
            projected,
            levels=levels,
            colors=["#2c7fb8", "#045a8d"][: len(levels)],
            linewidths=[0.8, 1.4][: len(levels)],
            zorder=3,
        )
    return levels


def export_mining_population_overlay() -> list[dict[str, str]]:
    fig, ax = plt.subplots(figsize=(7.0, 8.4), constrained_layout=True)
    priority_base(ax)
    contour_levels = draw_population_contours(ax)
    mining_records = gpd.read_file(MINING).to_crs(maps.DST_CRS)
    mining_locations = collapse_mining_locations(mining_records)
    boundary = gpd.read_file(BOUNDARY, layer="peru_pilot_boundary").to_crs(maps.DST_CRS)
    inside_mining, nearby_mining = split_locations_by_boundary(mining_locations, boundary.geometry.iloc[0])
    if not inside_mining.empty:
        inside_mining.plot(
            ax=ax,
            marker="D",
            color="#111111",
            edgecolor="white",
            linewidth=0.55,
            markersize=28,
            zorder=5,
        )
    if not nearby_mining.empty:
        nearby_mining.plot(
            ax=ax,
            marker="D",
            facecolor="white",
            edgecolor="#111111",
            linewidth=0.8,
            markersize=30,
            zorder=5,
        )

    handles: list = priority_handles()
    for level, color, width in zip(contour_levels, ["#2c7fb8", "#045a8d"], [0.8, 1.4], strict=True):
        handles.append(Line2D([0], [0], color=color, linewidth=width, label=f"Population exposure contour {level:.1f}"))
    handles.extend(
        [
            Line2D(
                [0],
                [0],
                marker="D",
                color="none",
                markerfacecolor="#111111",
                markeredgecolor="white",
                markersize=6,
                label=f"INGEMMET locations inside boundary (n={len(inside_mining)})",
            ),
            Line2D(
                [0],
                [0],
                marker="D",
                color="none",
                markerfacecolor="white",
                markeredgecolor="#111111",
                markersize=6,
                label=f"INGEMMET locations near boundary (n={len(nearby_mining)})",
            ),
        ]
    )
    legend = ax.legend(
        handles=handles,
        title="Priority score and external context",
        loc="lower left",
        bbox_to_anchor=(0.055, 0.025),
        frameon=True,
        framealpha=0.94,
        facecolor="white",
        edgecolor="white",
        fontsize=7.4,
        title_fontsize=8.3,
    )
    legend._legend_box.align = "left"
    png, pdf = save(fig, "peru_priority_mining_population_overlay")
    source_note = (
        "Population exposure contours are model context; official INGEMMET points are an external "
        "post-PIM overlay and do not affect the priority score; "
        f"{len(mining_records)} source records collapse to {len(mining_locations)} unique locations "
        f"({len(inside_mining)} inside and {len(nearby_mining)} near the boundary)."
    )
    return [
        {
            "figure_id": "peru_priority_mining_population_overlay",
            "format": fmt,
            "path": rel(path),
            "claim_level": "diagnostic_only",
            "evidence_role": "external_mining_overlay_and_population_context",
            "pim_source": rel(PIM),
            "pim_sha256": sha256(PIM),
            "evidence_support_source": rel(EVIDENCE_SUPPORT),
            "evidence_support_sha256": sha256(EVIDENCE_SUPPORT),
            "population_source": rel(POPULATION_EXPOSURE),
            "population_sha256": sha256(POPULATION_EXPOSURE),
            "mining_source": rel(MINING),
            "mining_sha256": sha256(MINING),
            "boundary_source": rel(BOUNDARY),
            "boundary_sha256": sha256(BOUNDARY),
            "note": source_note,
        }
        for fmt, path in (("png", png), ("pdf", pdf))
    ]


def export_sinpad_diagnostic() -> list[dict[str, str]]:
    fig, ax = plt.subplots(figsize=(7.0, 8.4), constrained_layout=True)
    priority_base(ax)
    events = gpd.read_file(SINPAD).to_crs(maps.DST_CRS)
    unique_events = collapse_sinpad_locations(events)
    flood_locations = unique_events[unique_events["is_flood_specific"].astype(bool)]
    unique_events.plot(
        ax=ax,
        marker="o",
        facecolor="none",
        edgecolor="#111111",
        linewidth=1.0,
        markersize=44,
        zorder=5,
    )
    if not flood_locations.empty:
        flood_locations.plot(
            ax=ax,
            marker="*",
            color="#00ffff",
            edgecolor="#111111",
            linewidth=0.7,
            markersize=105,
            zorder=6,
        )

    handles: list = priority_handles()
    handles.extend(
        [
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor="none",
                markeredgecolor="#111111",
                markersize=6,
                label=f"Unique hydrometeorological event locations (n={len(unique_events)})",
            ),
            Line2D(
                [0],
                [0],
                marker="*",
                color="none",
                markerfacecolor="#00ffff",
                markeredgecolor="#111111",
                markersize=9,
                label=f"Flood-specific event locations (n={len(flood_locations)})",
            ),
        ]
    )
    legend = ax.legend(
        handles=handles,
        title="SINPAD co-location diagnostic only",
        loc="lower left",
        bbox_to_anchor=(0.055, 0.025),
        frameon=True,
        framealpha=0.94,
        facecolor="white",
        edgecolor="white",
        fontsize=7.4,
        title_fontsize=8.3,
    )
    legend._legend_box.align = "left"
    png, pdf = save(fig, "peru_sinpad_colocation_diagnostic")
    return [
        {
            "figure_id": "peru_sinpad_colocation_diagnostic",
            "format": fmt,
            "path": rel(path),
            "claim_level": SINPAD_CLAIM_LEVEL,
            "evidence_role": "event_point_colocation_context",
            "pim_source": rel(PIM),
            "pim_sha256": sha256(PIM),
            "evidence_support_source": rel(EVIDENCE_SUPPORT),
            "evidence_support_sha256": sha256(EVIDENCE_SUPPORT),
            "event_source": rel(SINPAD),
            "event_sha256": sha256(SINPAD),
            "boundary_source": rel(BOUNDARY),
            "boundary_sha256": sha256(BOUNDARY),
            "note": SINPAD_NOTE,
        }
        for fmt, path in (("png", png), ("pdf", pdf))
    ]


def write_index(rows: list[dict[str, str]]) -> None:
    fields: list[str] = []
    for row in rows:
        row["output_sha256"] = sha256(ROOT / row["path"])
        for key in row:
            if key not in fields:
                fields.append(key)
    with (OUT_DIR / "index.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    require_inputs()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = export_mining_population_overlay()
    rows.extend(export_sinpad_diagnostic())
    write_index(rows)
    print(f"wrote {len(rows)} governed evidence-overlay outputs to {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
