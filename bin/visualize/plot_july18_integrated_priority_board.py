#!/usr/bin/env python3
"""Build the July 18 mentor-facing integrated priority board.

This is the single main figure for the 7/18 mentor preview. It carries the
mentor's three asks at once:

1. bilateral comparison (Zimbabwe Upper Mzingwane vs Peru engineering pilot, side by side);
2. per-pixel priority-criterion colouring (the "pixel colouring" she asked for);
3. a clear one-line takeaway stating *why* the two sites differ.

Layout: four panels. Top row = dominant priority driver per pixel (colour
codes the criterion contributing the largest share). Bottom row = top-20%
hotspot frequency (how often each cell lands in the high-priority set across
sensitivity scenarios). The claim level is printed on the figure face, not only
in the caption, so the image survives being forwarded without its caption.

The dominant-criterion computation reuses the verified logic from
``plot_mentor_boss_priority_explanation_package.py``. The hotspot frequency
rasters are read from the existing priority-scenario outputs. No criteria are
regenerated and no overlay is re-run.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FuncFormatter


ROOT = Path(__file__).resolve().parents[2]
INPUTS = [
    ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/scenario_weights.csv",
    ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/top20_frequency.tif",
    ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenario_weights.csv",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/top20_frequency.tif",
    ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
]
OUTPUTS = [
    ROOT / "outputs/zimbabwe_peru_prototype_comparison/july18_integrated_priority_board.png",
    ROOT / "outputs/zimbabwe_peru_prototype_comparison/july18_integrated_priority_board.pdf",
    ROOT / "outputs/zimbabwe_peru_prototype_comparison/july18_dominant_criterion_share.csv",
    ROOT / "outputs/zimbabwe_peru_prototype_comparison/july18_board_caption.md",
]
OUT_DIR = ROOT / "outputs/zimbabwe_peru_prototype_comparison"


# Colourblind-safe palette, shared with the mentor-explanation package so the
# two packs read the same way.
COLORS = {
    "flood": "#0072B2",
    "sediment": "#D55E00",
    "land_cover": "#009E73",
    "mining": "#CC79A7",
    "exposure": "#E69F00",
    "rainfall": "#F0E442",
}

FLOOD_CONDITIONING_LABEL = "Flood conditioning factors"
SOIL_EROSION_LABEL = "Soil erosion factors"
LULC_LABEL = "Land use/land cover"
MINING_LABEL = "Mining / ASM activity"
EXPOSURE_LABEL = "Exposure indicators"
RAINFALL_LABEL = "Rainfall"


@dataclass(frozen=True)
class Criterion:
    key: str
    family: str
    label: str
    path: Path
    claim_level: str


@dataclass(frozen=True)
class Site:
    label: str
    short_label: str
    boundary_id: str
    experiment_id: str
    criteria: tuple[Criterion, ...]
    weights_csv: Path
    hotspot_frequency: Path
    boundary_gpkg: Path
    boundary_layer: str
    crs_label: str
    claim_level: str
    status_note: str


SITES = [
    Site(
        label="Zimbabwe Upper Mzingwane",
        short_label="Zimbabwe",
        boundary_id="boundary_v1",
        experiment_id="rainfall_exposure_v0_4",
        weights_csv=ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/scenario_weights.csv",
        hotspot_frequency=ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/top20_frequency.tif",
        boundary_gpkg=ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg",
        boundary_layer="v1_working_boundary",
        crs_label="EPSG:32735",
        claim_level="sensitivity_scenario",
        status_note="controlled prototype boundary; not final thesis boundary",
        criteria=(
            Criterion("flood_conditioning_factors", "flood", FLOOD_CONDITIONING_LABEL, ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria/flood_conditioning_factors_0_1.tif", "provisional"),
            Criterion("soil_erosion_factors", "sediment", SOIL_EROSION_LABEL, ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria/soil_erosion_factors_0_1.tif", "diagnostic_only"),
            Criterion("land_cover_pressure", "land_cover", LULC_LABEL, ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria/land_cover_pressure_0_1.tif", "provisional"),
            Criterion("mining_pressure", "mining", MINING_LABEL, ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria/mining_pressure_0_1.tif", "diagnostic_only"),
            Criterion("exposure_indicators", "exposure", EXPOSURE_LABEL, ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria/exposure_indicators_0_1.tif", "diagnostic_only"),
            Criterion("rainfall_climatology", "rainfall", RAINFALL_LABEL, ROOT / "outputs/boundary_v1/rainfall_sensitivity_v0_3/criteria/rainfall_climatology_0_1_PROVISIONAL_30m.tif", "sensitivity_scenario"),
        ),
    ),
    Site(
        label="Peru pilot site",
        short_label="Peru",
        boundary_id="PE1",
        experiment_id="priority_scenarios",
        weights_csv=ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenario_weights.csv",
        hotspot_frequency=ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/top20_frequency.tif",
        boundary_gpkg=ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
        boundary_layer="peru_pilot_boundary",
        crs_label="EPSG:32718",
        claim_level="engineering_pilot / sensitivity_scenario",
        status_note="temporary pilot site; replace if mentor names another Peru site",
        criteria=(
            Criterion("flood_conditioning_factors", "flood", FLOOD_CONDITIONING_LABEL, ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/flood_conditioning_factors_0_1.tif", "provisional"),
            Criterion("soil_erosion_factors", "sediment", SOIL_EROSION_LABEL, ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/soil_erosion_factors_0_1.tif", "diagnostic_only"),
            Criterion("land_cover_pressure", "land_cover", LULC_LABEL, ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/land_cover_pressure_0_1.tif", "provisional"),
            Criterion("mining_pressure", "mining", MINING_LABEL, ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/mining_pressure_0_1.tif", "provisional"),
            Criterion("exposure_indicators", "exposure", EXPOSURE_LABEL, ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/exposure_indicators_0_1.tif", "provisional"),
            Criterion("rainfall_climatology", "rainfall", RAINFALL_LABEL, ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/rainfall_climatology_0_1.tif", "sensitivity_scenario"),
        ),
    ),
]


def read_weights(path: Path, experiment_id: str) -> dict[str, float]:
    """Mean weight per criterion across the scenarios of one experiment."""
    rows: dict[str, list[float]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["experiment_id"] != experiment_id:
                continue
            rows.setdefault(row["criterion"], []).append(float(row["weight"]))
    if not rows:
        raise ValueError(f"No weights for experiment {experiment_id}: {path}")
    return {criterion: float(np.mean(values)) for criterion, values in rows.items()}


def read_raster(path: Path, profile: dict | None = None) -> tuple[np.ndarray, dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    with rasterio.open(path) as src:
        if profile is not None:
            if src.crs != profile["crs"] or src.transform != profile["transform"]:
                raise ValueError(f"grid mismatch: {path}")
            if src.width != profile["width"] or src.height != profile["height"]:
                raise ValueError(f"shape mismatch: {path}")
        data = src.read(1).astype("float32")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
        data[~np.isfinite(data)] = np.nan
        out_profile = src.profile.copy()
    return data, out_profile


def normalize_if_needed(data: np.ndarray) -> np.ndarray:
    values = data[np.isfinite(data)]
    if values.size == 0:
        raise ValueError("empty raster")
    if float(values.min()) >= -0.000001 and float(values.max()) <= 1.000001:
        return np.clip(data, 0.0, 1.0).astype("float32")
    high = float(values.max())
    if high <= 0:
        raise ValueError("non-positive criterion")
    return np.clip(data / high, 0.0, 1.0).astype("float32")


def build_site_products(site: Site) -> dict[str, object]:
    """Compute the per-pixel dominant criterion. Mirrors the verified logic in
    ``plot_mentor_boss_priority_explanation_package.build_site_products``."""
    weights = read_weights(site.weights_csv, site.experiment_id)
    arrays: list[np.ndarray] = []
    profile = None
    for criterion in site.criteria:
        raw, profile = read_raster(criterion.path, profile)
        arrays.append(normalize_if_needed(raw))
    assert profile is not None

    stack = np.stack(arrays)
    valid = np.all(np.isfinite(stack), axis=0)
    mean_weights = np.array([weights[c.key] for c in site.criteria], dtype="float32")
    contributions = stack * mean_weights[:, None, None]
    winner = np.nanargmax(np.where(valid[None, :, :], contributions, -np.inf), axis=0)
    dominant = np.full(valid.shape, np.nan, dtype="float32")
    dominant[valid] = winner[valid].astype("float32") + 1.0

    hotspot, hotspot_profile = read_raster(site.hotspot_frequency)
    # The hotspot raster should share the criteria grid; if it does not, mask
    # rather than fail so the figure still renders with a recorded warning.
    grid_ok = (
        hotspot_profile["width"] == profile["width"]
        and hotspot_profile["height"] == profile["height"]
    )

    # Dominant-criterion pixel share, for the takeaway line and the CSV.
    share_rows = []
    for idx, criterion in enumerate(site.criteria):
        code = idx + 1
        share_rows.append({
            "site": site.short_label,
            "boundary_id": site.boundary_id,
            "criterion_code": code,
            "criterion_family": criterion.family,
            "criterion_label": criterion.label,
            "dominant_pixel_share": round(float(np.mean(dominant[valid] == code)), 6),
            "claim_level": criterion.claim_level,
        })

    return {
        "site": site,
        "profile": profile,
        "dominant": dominant,
        "hotspot": hotspot if grid_ok else None,
        "hotspot_grid_ok": grid_ok,
        "share_rows": share_rows,
    }


def map_extent(profile: dict) -> tuple[float, float, float, float]:
    bounds = rasterio.transform.array_bounds(profile["height"], profile["width"], profile["transform"])
    return (bounds[0], bounds[2], bounds[1], bounds[3])


def format_map_axes(ax, site: Site, profile: dict) -> None:
    boundary = gpd.read_file(site.boundary_gpkg, layer=site.boundary_layer).to_crs(profile["crs"])
    boundary.boundary.plot(ax=ax, color="black", linewidth=0.9)
    formatter = FuncFormatter(lambda value, _: f"{value / 1000:.0f}")
    ax.xaxis.set_major_formatter(formatter)
    ax.yaxis.set_major_formatter(formatter)
    ax.set_xlabel(f"Easting (km, {site.crs_label})", fontsize=8)
    ax.set_ylabel("Northing (km)", fontsize=8)
    ax.grid(color="0.9", linewidth=0.35)
    ax.tick_params(labelsize=8)


def top_driver_label(share_rows: list[dict[str, object]]) -> str:
    """Plain-English top driver for one site, e.g. 'Rainfall (38.2%)'."""
    ordered = sorted(share_rows, key=lambda r: float(r["dominant_pixel_share"]), reverse=True)
    top = ordered[0]
    pct = float(top["dominant_pixel_share"]) * 100
    return f"{top['criterion_label']} ({pct:.0f}%)"


def build_takeaway(products_by_site: list[dict[str, object]]) -> str:
    """One-sentence takeaway across both sites. A statement, not a question."""
    parts = []
    for products in products_by_site:
        site: Site = products["site"]  # type: ignore[assignment]
        parts.append(f"{site.short_label}: {top_driver_label(products['share_rows'])}")  # type: ignore[index]
    return "Top driver of the prototype priority score — " + " vs ".join(parts) + " of pixels."


def write_share_csv(path: Path, all_rows: list[dict[str, object]]) -> None:
    fields = ["site", "boundary_id", "criterion_code", "criterion_family",
              "criterion_label", "dominant_pixel_share", "claim_level"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_rows)


def plot_board(products_by_site: list[dict[str, object]]) -> None:
    cmap = ListedColormap([COLORS[c.family] for c in SITES[0].criteria])
    norm = BoundaryNorm(np.arange(0.5, 7.5, 1), cmap.N)

    fig = plt.figure(figsize=(13.8, 13.2))
    # Title row, true 2x2 map layout, legend row, status row.
    grid = fig.add_gridspec(
        5, 2,
        height_ratios=[0.09, 1.0, 1.0, 0.12, 0.055],
        hspace=0.34, wspace=0.16,
        left=0.055, right=0.96, top=0.965, bottom=0.05,
    )

    title_ax = fig.add_subplot(grid[0, :])
    title_ax.set_axis_off()
    takeaway = build_takeaway(products_by_site)
    title_ax.text(0.5, 0.5, takeaway, ha="center", va="center",
                  fontsize=14.5, fontweight="bold", wrap=True)

    panel_letters = {
        (0, 0): "A",
        (0, 1): "B",
        (1, 0): "C",
        (1, 1): "D",
    }

    for col, products in enumerate(products_by_site):
        site: Site = products["site"]  # type: ignore[assignment]
        profile: dict = products["profile"]  # type: ignore[assignment]
        dominant: np.ndarray = products["dominant"]  # type: ignore[assignment]

        # Top row: dominant criterion (pixel colouring).
        ax_top = fig.add_subplot(grid[1, col])
        ax_top.imshow(np.ma.masked_invalid(dominant), extent=map_extent(profile),
                      origin="upper", cmap=cmap, norm=norm, aspect="equal")
        format_map_axes(ax_top, site, profile)
        ax_top.set_title(f"{panel_letters[(0, col)]}. {site.short_label} — dominant priority driver",
                         loc="left", fontsize=12.5, fontweight="bold", pad=8)
        ax_top.set_xlabel("")
        ax_top.tick_params(labelbottom=False)

        # Bottom row: top-20% hotspot frequency.
        ax_bot = fig.add_subplot(grid[2, col])
        hotspot: np.ndarray | None = products["hotspot"]  # type: ignore[assignment]
        if hotspot is not None:
            im = ax_bot.imshow(np.ma.masked_invalid(hotspot), extent=map_extent(profile),
                               origin="upper", cmap="inferno", vmin=0, vmax=1, aspect="equal")
            bbox = ax_bot.get_position()
            cax = fig.add_axes([
                bbox.x1 + 0.006,
                bbox.y0 + bbox.height * 0.12,
                0.010,
                bbox.height * 0.76,
            ])
            cb = fig.colorbar(im, cax=cax)
            cb.set_label("top-20% frequency", fontsize=8)
            cb.ax.tick_params(labelsize=7)
        else:
            ax_bot.text(0.5, 0.5, "hotspot grid mismatch — not plotted",
                        ha="center", va="center", transform=ax_bot.transAxes, fontsize=9)
        format_map_axes(ax_bot, site, profile)
        ax_bot.set_title(f"{panel_letters[(1, col)]}. {site.short_label} — top-20% priority hotspot frequency",
                         loc="left", fontsize=12.5, fontweight="bold", pad=8)

    # Legend row: one Patch per criterion family.
    legend_ax = fig.add_subplot(grid[3, :])
    legend_ax.set_axis_off()
    handles = [Patch(facecolor=COLORS[c.family], edgecolor="0.3",
                     label=f"{i + 1}. {c.label}") for i, c in enumerate(SITES[0].criteria)]
    legend_ax.legend(handles=handles, loc="center", ncol=6, frameon=True, fontsize=9.5)

    # Claim level on the figure face, bottom-left, plain language.
    fig.text(
        0.02, 0.012,
        "Prototype / sensitivity scenario — not a final flood-risk map, not a final "
        "Zimbabwe–Peru comparison. Peru is an engineering pilot site.",
        fontsize=9.5, color="0.25", ha="left", va="bottom",
    )

    fig.savefig(OUT_DIR / "july18_integrated_priority_board.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT_DIR / "july18_integrated_priority_board.pdf", bbox_inches="tight")
    plt.close(fig)


def write_caption(path: Path, products_by_site: list[dict[str, object]]) -> None:
    takeaway = build_takeaway(products_by_site)
    lines = [
        "# Caption",
        "",
        "Fig. X. Integrated prototype priority board for the 18 July mentor preview. "
        "Top row: each pixel is coloured by the criterion family that contributes the largest share "
        "to the prototype priority score under the current sensitivity scenarios. "
        "Bottom row: how often each cell appears in the top-20% priority hotspot set across scenarios. "
        "Left column: Zimbabwe Upper Mzingwane prototype catchment. "
        "Right column: Peru engineering-pilot site.",
        "",
        f"Takeaway: {takeaway}",
        "",
        "Status: prototype / sensitivity scenario. These maps explain which criteria drive "
        "the current prototype score and where stable hotspots sit. They are not a validated "
        "flood-risk map, not an intervention-priority map, and not a final Zimbabwe–Peru "
        "comparison. Peru is an engineering pilot and will be replaced if the mentor names a "
        "specific Peru site.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    products_by_site = []
    all_share_rows = []
    for site in SITES:
        products = build_site_products(site)
        products_by_site.append(products)
        all_share_rows.extend(products["share_rows"])  # type: ignore[arg-type]
    write_share_csv(OUT_DIR / "july18_dominant_criterion_share.csv", all_share_rows)
    plot_board(products_by_site)
    write_caption(OUT_DIR / "july18_board_caption.md", products_by_site)
    print(f"Wrote July 18 integrated priority board to {OUT_DIR}")


if __name__ == "__main__":
    main()
