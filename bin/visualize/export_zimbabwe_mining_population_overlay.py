#!/usr/bin/env python3
"""Export Zimbabwe priority with independent mining and population context."""

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
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds
from scipy.ndimage import gaussian_filter


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bin/visualize"))

import export_paper_style_single_maps as maps


PIM = ROOT / (
    "outputs/zimbabwe_pim_scenarios/rainfall_exposure/scenarios/"
    "priority_mentor_zimbabwe_direct_pim.tif"
)
POPULATION = ROOT / (
    "data/raw/worldpop_2020_zimbabwe/zwe_ppp_2020_UNadj.tif"
)
MINING_FOOTPRINTS = ROOT / (
    "data/raw/global_mining_polygons_v2_zimbabwe/global_mining_polygons_v2.gpkg"
)
BOUNDARY = ROOT / "outputs/zimbabwe_boundary/zimbabwe_boundary.gpkg"
OUT_DIR = ROOT / "outputs/slide_ready_figures/zimbabwe_evidence_overlays"
PNG = OUT_DIR / "zimbabwe_priority_mining_population_overlay_no_title_caption.png"
PDF = PNG.with_suffix(".pdf")
CLIPPED_FOOTPRINTS = OUT_DIR / "zimbabwe_mapped_mining_footprints.gpkg"
INDEX = OUT_DIR / "index.csv"
SOURCE_ASSESSMENT = OUT_DIR / "source_assessment.csv"
OUTPUTS = [PNG, PDF, CLIPPED_FOOTPRINTS, INDEX, SOURCE_ASSESSMENT]

SITE = maps.Site(
    slug="zimbabwe",
    label="Zimbabwe Upper Mzingwane controlled prototype catchment",
    claim_level="diagnostic_only",
    priority_mean=PIM,
    flood_conditioning=ROOT / (
        "outputs/zimbabwe_pim_scenarios/rainfall_exposure/pim_criteria/"
        "flood_hazard_0_1.tif"
    ),
    boundary_gpkg=BOUNDARY,
    boundary_layer="v1_working_boundary",
)

POPULATION_LEVELS = (0.35, 0.60)
POPULATION_COLORS = ("#2c7fb8", "#045a8d")


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def require_inputs() -> None:
    missing = [path for path in (PIM, POPULATION, MINING_FOOTPRINTS, BOUNDARY) if not path.exists()]
    if missing:
        raise FileNotFoundError("missing Zimbabwe overlay inputs: " + ", ".join(map(str, missing)))


def clip_mining_footprints() -> gpd.GeoDataFrame:
    mining = gpd.read_file(MINING_FOOTPRINTS)
    mining = mining[mining["ISO3_CODE"].eq("ZWE")].copy()
    boundary = gpd.read_file(BOUNDARY, layer="v1_working_boundary").to_crs(mining.crs)
    clipped = gpd.overlay(mining, boundary[["geometry"]], how="intersection", keep_geom_type=True)
    clipped = clipped[~clipped.geometry.is_empty].copy()
    clipped["mapped_area_km2"] = clipped.to_crs("EPSG:32735").area / 1_000_000
    if CLIPPED_FOOTPRINTS.exists():
        CLIPPED_FOOTPRINTS.unlink()
    clipped.to_file(CLIPPED_FOOTPRINTS, layer="mapped_mining_footprints", driver="GPKG")
    return clipped


def draw_priority(ax) -> float:
    priority, profile = maps.read_raster(PIM)
    classes = maps.classify_equal_interval(priority, maps.PRIORITY_BOUNDS)
    projected, extent = maps.reproject_class(classes, profile)
    frame_extent = maps.frame_extent_for_legend(extent)
    masked = np.ma.masked_where(projected == 0, projected)
    cmap = ListedColormap(maps.PRIORITY_COLORS)
    norm = BoundaryNorm(
        np.arange(0.5, len(maps.PRIORITY_COLORS) + 1.5),
        len(maps.PRIORITY_COLORS),
    )
    ax.imshow(
        masked,
        extent=extent,
        origin="upper",
        cmap=cmap,
        norm=norm,
        interpolation="nearest",
        zorder=1,
    )
    boundary = gpd.read_file(BOUNDARY, layer="v1_working_boundary").to_crs(profile["crs"])
    inside = geometry_mask(
        boundary.geometry,
        out_shape=priority.shape,
        transform=profile["transform"],
        invert=True,
    )
    valid = inside & np.isfinite(priority)
    unscored = (inside & ~np.isfinite(priority)).astype("uint8")
    unscored_projected, unscored_extent = maps.reproject_class(unscored, profile)
    if unscored_extent != extent:
        raise ValueError("unscored PIM extent does not match priority extent")
    overlay = np.ma.masked_where(unscored_projected != 1, unscored_projected)
    ax.contourf(
        overlay,
        levels=[0.5, 1.5],
        colors="none",
        hatches=["////"],
        extent=extent,
        origin="upper",
        zorder=2,
    )
    maps.add_boundary_and_frame(ax, SITE, frame_extent)
    maps.add_north_arrow(ax)
    maps.add_scale_bar(ax, frame_extent)
    return float(valid.sum() / inside.sum())


def read_boundary_population() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    boundary = gpd.read_file(BOUNDARY, layer="v1_working_boundary")
    with rasterio.open(POPULATION) as src:
        projected_boundary = boundary.to_crs(src.crs)
        west, south, east, north = projected_boundary.total_bounds
        window = from_bounds(west, south, east, north, src.transform).round_offsets().round_lengths()
        data = src.read(1, window=window).astype("float32")
        transform = src.window_transform(window)
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
        data[data < 0] = np.nan
        inside = geometry_mask(
            projected_boundary.geometry,
            out_shape=data.shape,
            transform=transform,
            invert=True,
        )
        data[~inside] = np.nan
        x = transform.c + (np.arange(data.shape[1]) + 0.5) * transform.a
        y = transform.f + (np.arange(data.shape[0]) + 0.5) * transform.e
    return x, y, data, inside


def draw_population(ax) -> tuple[list[float], float]:
    x, y, population, inside = read_boundary_population()
    valid = np.isfinite(population)
    weights = gaussian_filter(valid.astype("float32"), sigma=5.0, mode="constant")
    smoothed = gaussian_filter(np.nan_to_num(population), sigma=5.0, mode="constant")
    smoothed = np.divide(
        smoothed,
        weights,
        out=np.full_like(smoothed, np.nan),
        where=weights > 0.05,
    )
    smoothed[~valid] = np.nan
    finite = smoothed[np.isfinite(smoothed)]
    levels = [level for level in POPULATION_LEVELS if finite.min() < level < finite.max()]
    if levels:
        ax.contour(
            x,
            y,
            smoothed,
            levels=levels,
            colors=POPULATION_COLORS[: len(levels)],
            linewidths=(0.85, 1.35)[: len(levels)],
            zorder=3,
        )
    return levels, float(valid.sum() / inside.sum())


def export_overlay(footprints: gpd.GeoDataFrame) -> list[dict[str, object]]:
    fig, ax = plt.subplots(figsize=(7.0, 8.4), constrained_layout=True)
    pim_coverage = draw_priority(ax)
    levels, population_valid_fraction = draw_population(ax)
    footprints.to_crs(maps.DST_CRS).plot(
        ax=ax,
        facecolor="#b2188b",
        edgecolor="#6a0055",
        linewidth=1.5,
        alpha=0.96,
        zorder=5,
    )

    handles: list = [
        Patch(facecolor=color, edgecolor="0.4", label=label)
        for label, color in zip(maps.PRIORITY_LABELS, maps.PRIORITY_COLORS, strict=True)
    ]
    handles.append(
        Patch(facecolor="#d9d9d9", edgecolor="#555555", hatch="////", label="Unscored: incomplete criterion evidence")
    )
    handles.extend(
        Line2D(
            [0],
            [0],
            color=color,
            linewidth=width,
            label=f"Smoothed WorldPop context: {level:.2f} persons per ~100 m cell",
        )
        for level, color, width in zip(
            levels,
            POPULATION_COLORS[: len(levels)],
            (0.85, 1.35)[: len(levels)],
            strict=True,
        )
    )
    handles.append(
        Patch(
            facecolor="#b2188b",
            edgecolor="#6a0055",
            label=f"Mapped mining land-use footprints (non-exhaustive, n={len(footprints)})",
        )
    )
    legend = ax.legend(
        handles=handles,
        title="Priority score and spatial context",
        loc="lower left",
        bbox_to_anchor=(0.055, 0.025),
        frameon=True,
        framealpha=0.95,
        facecolor="white",
        edgecolor="white",
        fontsize=7.4,
        title_fontsize=8.3,
    )
    legend._legend_box.align = "left"
    fig.savefig(PNG, dpi=300, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(PDF, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)

    area_km2 = float(footprints["mapped_area_km2"].sum())
    note = (
        "WorldPop population and non-exhaustive satellite-interpreted mining land use are independent context; "
        "not official mining titles, verified active ASM sites, affected population, or flood validation."
    )
    return [
        {
            "figure_id": "zimbabwe_priority_mining_population_overlay",
            "format": path.suffix.lstrip("."),
            "path": rel(path),
            "claim_level": "diagnostic_only",
            "evidence_role": "independent_context",
            "pim_source": rel(PIM),
            "pim_sha256": sha256(PIM),
            "population_source": rel(POPULATION),
            "population_sha256": sha256(POPULATION),
            "mining_source": rel(MINING_FOOTPRINTS),
            "mining_sha256": sha256(MINING_FOOTPRINTS),
            "mapped_mining_footprints": len(footprints),
            "mapped_mining_area_km2": f"{area_km2:.6f}",
            "population_display_method": "WorldPop native counts smoothed with a 500 m Gaussian kernel for contour display only",
            "population_contour_levels_persons_per_cell": ";".join(f"{level:.2f}" for level in levels),
            "population_contour_basis": "fixed reference contours near the upper decile and upper 2.5 percent of the boundary distribution",
            "population_valid_fraction": f"{population_valid_fraction:.8f}",
            "pim_coverage_fraction": f"{pim_coverage:.8f}",
            "boundary_source": rel(BOUNDARY),
            "boundary_sha256": sha256(BOUNDARY),
            "note": note,
        }
        for path in (PNG, PDF)
    ]


def source_assessment_rows() -> list[dict[str, str]]:
    return [
        {
            "source": "Global Mining Polygons v2",
            "role": "mapped mining land-use footprint",
            "status": "selected",
            "coverage": "six mapped polygons intersect the working boundary",
            "limitation": "non-exhaustive 2019 satellite interpretation around source mining coordinates; no mining type, title, operator or active-status fields",
            "url": "https://doi.org/10.1594/PANGAEA.942325",
        },
        {
            "source": "WorldPop Zimbabwe 2020",
            "role": "population distribution",
            "status": "selected",
            "coverage": "approximately 99.5% valid boundary coverage at approximately 100 m",
            "limitation": "modelled population count, not observed flood-affected population",
            "url": "https://hub.worldpop.org/",
        },
        {
            "source": "GHSL population and built-up surface 2025",
            "role": "population and settlement cross-check",
            "status": "available cross-check",
            "coverage": "complete Zimbabwe coverage at 100 m",
            "limitation": "reserved for independent cross-check to avoid visual clutter",
            "url": "https://human-settlement.emergency.copernicus.eu/",
        },
        {
            "source": "USGS Africa GIS mineral industries",
            "role": "mineral facility and deposit reference",
            "status": "supporting context",
            "coverage": "Zimbabwe records available",
            "limitation": "reference locations are not mapped active mining footprints",
            "url": "https://doi.org/10.5066/P97EQWXP",
        },
        {
            "source": "Zimbabwe Mining Cadastre",
            "role": "official mining titles",
            "status": "not openly usable",
            "coverage": "public map/download unavailable; records described as provisional",
            "limitation": "registration and official verification required",
            "url": "http://portal.miningcadastre.org/zw/",
        },
        {
            "source": "IPIS Runde Valley ASM site visits 2019",
            "role": "visited ASM sites",
            "status": "not used",
            "coverage": "Runde Valley survey; boundary overlap not established",
            "limitation": "WFS endpoint unavailable during 2026-07-14 check",
            "url": "https://data.humdata.org/dataset/zwe_mines_curated_all_opendata_p_ipis",
        },
    ]


def main() -> None:
    require_inputs()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    footprints = clip_mining_footprints()
    rows = export_overlay(footprints)
    write_csv(INDEX, rows)
    write_csv(SOURCE_ASSESSMENT, source_assessment_rows())
    print(
        f"exported Zimbabwe mining/population overlay with {len(footprints)} mapped footprints "
        f"to {rel(OUT_DIR)}"
    )


if __name__ == "__main__":
    main()
