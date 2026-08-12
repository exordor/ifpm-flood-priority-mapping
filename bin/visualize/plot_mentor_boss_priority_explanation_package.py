#!/usr/bin/env python3
"""Create presentation-ready colour-coded priority-criteria explanation figures."""

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
from mpl_toolkits.axes_grid1 import make_axes_locatable


ROOT = Path(__file__).resolve().parents[2]
INPUTS = [ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/scenario_weights.csv", ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg", ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenario_weights.csv", ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"]
OUTPUTS = [ROOT / "outputs/mentor_boss_priority_explanation/dominant_priority_criterion_maps.png", ROOT / "outputs/mentor_boss_priority_explanation/mentor_boss_priority_explanation_handoff.md"]
import sys
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import write_raster as _write_raster
from _lib.standardization import ensure_unit_interval
from functools import partial
write_raster = partial(_write_raster, sanitize=True)
normalize_if_needed = ensure_unit_interval
OUT_DIR = ROOT / "outputs/mentor_boss_priority_explanation"
NODATA = -9999.0


COLORS = {
    "flood": "#0072B2",
    "sediment": "#D55E00",
    "landuse_asm": "#009E73",
    "environmental": "#CC79A7",
    "socioeconomic": "#E69F00",
}

FLOOD_LABEL = "Flood hazard"
SEDIMENT_LABEL = "Sediment"
LANDUSE_ASM_LABEL = "Land Use / ASM"
ENVIRONMENTAL_LABEL = "Environmental sensitivity"
SOCIOECONOMIC_LABEL = "Socioeconomic exposure"


@dataclass(frozen=True)
class Criterion:
    key: str
    family: str
    label: str
    path: Path
    claim_level: str
    limitation: str


@dataclass(frozen=True)
class Site:
    label: str
    short_label: str
    boundary_id: str
    experiment_id: str
    criteria: tuple[Criterion, ...]
    weights_csv: Path
    boundary_gpkg: Path
    boundary_layer: str
    crs_label: str
    claim_level: str
    process_note: str


SITES = [
    Site(
        label="Zimbabwe Upper Mzingwane",
        short_label="Zimbabwe",
        boundary_id="boundary_v1",
        experiment_id="rainfall_exposure_v0_4",
        weights_csv=ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/scenario_weights.csv",
        boundary_gpkg=ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg",
        boundary_layer="v1_working_boundary",
        crs_label="EPSG:32735",
        claim_level="sensitivity_scenario",
        process_note="controlled prototype boundary; not final thesis boundary",
        criteria=(
            Criterion("flood_hazard", "flood", FLOOD_LABEL, ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/pim_criteria/flood_hazard_0_1.tif", "sensitivity_scenario", "flood conditioning plus coarse rainfall context; not inundation depth"),
            Criterion("sediment", "sediment", SEDIMENT_LABEL, ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/pim_criteria/sediment_0_1.tif", "diagnostic_only", "K x LS x C structure; rainfall erosivity not applied"),
            Criterion("landuse_asm", "landuse_asm", LANDUSE_ASM_LABEL, ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/pim_criteria/landuse_asm_0_1.tif", "provisional", "land-cover pressure plus mining-pressure indicator"),
            Criterion("environmental", "environmental", ENVIRONMENTAL_LABEL, ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/pim_criteria/environmental_0_1.tif", "provisional", "water/wetland context plus protected-area proximity"),
            Criterion("socioeconomic", "socioeconomic", SOCIOECONOMIC_LABEL, ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/pim_criteria/socioeconomic_0_1.tif", "diagnostic_only", "road access indicator, not observed vulnerability"),
        ),
    ),
    Site(
        label="Southern Peru comparison catchment",
        short_label="Peru",
        boundary_id="Arequipa Region",
        experiment_id="priority_scenarios",
        weights_csv=ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenario_weights.csv",
        boundary_gpkg=ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
        boundary_layer="peru_pilot_boundary",
        crs_label="EPSG:32718",
        claim_level="provisional / sensitivity_scenario",
        process_note="Arequipa Region, mainly Vitor-La Joya-Santa Rita de Siguas west of Arequipa city; final Peru study area remains open",
        criteria=(
            Criterion("flood_hazard", "flood", FLOOD_LABEL, ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/flood_hazard_0_1.tif", "sensitivity_scenario", "flood conditioning plus coarse rainfall context; not inundation depth"),
            Criterion("sediment", "sediment", SEDIMENT_LABEL, ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/sediment_0_1.tif", "diagnostic_only", "K x LS x C structure; rainfall erosivity not applied"),
            Criterion("landuse_asm", "landuse_asm", LANDUSE_ASM_LABEL, ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/landuse_asm_0_1.tif", "provisional", "land-cover pressure plus official mining-point proximity"),
            Criterion("environmental", "environmental", ENVIRONMENTAL_LABEL, ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/environmental_0_1.tif", "provisional", "water/wetland context plus protected-area proximity"),
            Criterion("socioeconomic", "socioeconomic", SOCIOECONOMIC_LABEL, ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/socioeconomic_0_1.tif", "provisional", "road access indicator, not observed vulnerability"),
        ),
    ),
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def read_weights(path: Path, experiment_id: str) -> dict[str, float]:
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


def build_site_products(site: Site) -> tuple[dict[str, object], list[dict[str, object]]]:
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
    contribution_sum = np.nansum(np.where(valid[None, :, :], contributions, np.nan), axis=0)
    contribution_sum[~valid] = np.nan
    shares = contributions / contribution_sum[None, :, :]
    shares[:, ~valid] = np.nan

    dominant = np.full(valid.shape, np.nan, dtype="float32")
    dominant_strength = np.full(valid.shape, np.nan, dtype="float32")
    winner = np.nanargmax(np.where(valid[None, :, :], contributions, -np.inf), axis=0)
    dominant[valid] = winner[valid].astype("float32") + 1.0
    dominant_strength[valid] = np.nanmax(shares[:, valid], axis=0).astype("float32")

    site_dir = OUT_DIR / site.short_label.lower()
    write_raster(site_dir / "dominant_criterion_code.tif", dominant, profile)
    write_raster(site_dir / "dominant_criterion_strength.tif", dominant_strength, profile)
    for idx, criterion in enumerate(site.criteria):
        write_raster(site_dir / f"contribution_share_{criterion.family}.tif", shares[idx], profile)

    manifest_rows = []
    valid_count = int(valid.sum())
    inside_count = int(np.logical_or.reduce([np.isfinite(a) for a in stack]).sum())
    for idx, criterion in enumerate(site.criteria):
        criterion_values = stack[idx][np.isfinite(stack[idx])]
        share_values = shares[idx][valid]
        manifest_rows.append({
            "site": site.short_label,
            "boundary_id": site.boundary_id,
            "experiment_id": site.experiment_id,
            "criterion_code": idx + 1,
            "criterion_family": criterion.family,
            "criterion_label": criterion.label,
            "colour_hex": COLORS[criterion.family],
            "source_raster": rel(criterion.path),
            "mean_scenario_weight": round(float(mean_weights[idx]), 6),
            "criterion_mean_0_1": round(float(np.nanmean(criterion_values)), 6),
            "mean_contribution_share": round(float(np.nanmean(share_values)), 6),
            "dominant_pixel_share": round(float(np.mean(dominant[valid] == idx + 1)), 6),
            "claim_level": criterion.claim_level,
            "limitation": criterion.limitation,
        })
    products = {
        "site": site,
        "profile": profile,
        "valid": valid,
        "dominant": dominant,
        "dominant_strength": dominant_strength,
        "shares": shares,
        "common_valid_fraction": valid_count / inside_count if inside_count else 0.0,
    }
    return products, manifest_rows


def add_colorbar(fig, ax, image, label: str) -> None:
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.08)
    cb = fig.colorbar(image, cax=cax)
    cb.ax.tick_params(labelsize=8)
    cb.set_label(label, fontsize=9)


def map_extent(profile: dict) -> tuple[float, float, float, float]:
    bounds = rasterio.transform.array_bounds(profile["height"], profile["width"], profile["transform"])
    return (bounds[0], bounds[2], bounds[1], bounds[3])


def format_map_axes(ax, site: Site, profile: dict) -> None:
    boundary = gpd.read_file(site.boundary_gpkg, layer=site.boundary_layer).to_crs(profile["crs"])
    boundary.boundary.plot(ax=ax, color="black", linewidth=0.8)
    formatter = FuncFormatter(lambda value, _: f"{value / 1000:.0f}")
    ax.xaxis.set_major_formatter(formatter)
    ax.yaxis.set_major_formatter(formatter)
    ax.set_xlabel(f"Easting (km, {site.crs_label})", fontsize=8)
    ax.set_ylabel("Northing (km)", fontsize=8)
    ax.grid(color="0.9", linewidth=0.35)
    ax.tick_params(labelsize=8)


def plot_dominant(products_by_site: list[dict[str, object]]) -> None:
    cmap = ListedColormap([COLORS[c.family] for c in SITES[0].criteria])
    norm = BoundaryNorm(np.arange(0.5, len(SITES[0].criteria) + 1.5, 1), cmap.N)
    fig = plt.figure(figsize=(12, 6.8), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.13])
    axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])]
    legend_ax = fig.add_subplot(grid[1, :])
    legend_ax.set_axis_off()
    for ax, products in zip(axes, products_by_site, strict=True):
        site: Site = products["site"]  # type: ignore[assignment]
        profile: dict = products["profile"]  # type: ignore[assignment]
        data: np.ndarray = products["dominant"]  # type: ignore[assignment]
        ax.imshow(np.ma.masked_invalid(data), extent=map_extent(profile), origin="upper", cmap=cmap, norm=norm)
        format_map_axes(ax, site, profile)
        ax.set_title(f"{site.short_label}: dominant priority driver", loc="left", fontsize=12, fontweight="bold")

    handles = [Patch(facecolor=COLORS[c.family], edgecolor="0.3", label=f"{i + 1}. {c.label}") for i, c in enumerate(SITES[0].criteria)]
    legend_ax.legend(handles=handles, loc="center", ncol=5, frameon=True, fontsize=9)
    fig.suptitle("Dominant driver of the prototype priority score", fontsize=14, fontweight="bold")
    fig.savefig(OUT_DIR / "dominant_priority_criterion_maps.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT_DIR / "dominant_priority_criterion_maps.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_contributions(products: dict[str, object]) -> None:
    site: Site = products["site"]  # type: ignore[assignment]
    profile: dict = products["profile"]  # type: ignore[assignment]
    shares: np.ndarray = products["shares"]  # type: ignore[assignment]
    fig, axes = plt.subplots(2, 3, figsize=(12.5, 8), constrained_layout=True)
    for idx, ax in enumerate(axes.ravel()):
        if idx >= len(site.criteria):
            ax.set_axis_off()
            continue
        criterion = site.criteria[idx]
        image = ax.imshow(
            np.ma.masked_invalid(shares[idx]),
            extent=map_extent(profile),
            origin="upper",
            cmap="viridis",
            vmin=0,
            vmax=0.7,
        )
        format_map_axes(ax, site, profile)
        ax.set_title(criterion.label, loc="left", fontsize=10, fontweight="bold", color=COLORS[criterion.family])
        add_colorbar(fig, ax, image, "share")
    fig.suptitle(f"{site.label}: criterion contribution share maps", fontsize=14, fontweight="bold")
    out_base = OUT_DIR / f"{site.short_label.lower()}_criteria_contribution_maps"
    fig.savefig(out_base.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(out_base.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def plot_process() -> None:
    fig, ax = plt.subplots(figsize=(8.4, 10.3))
    ax.set_axis_off()

    # Goal header: why this analysis exists for a non-specialist review audience.
    goal_y = 0.945
    ax.add_patch(Rectangle((0.09, goal_y - 0.075), 0.82, 0.075, facecolor="#2A9D8F", edgecolor="none"))
    ax.text(0.5, goal_y - 0.0375, "Goal: identify which criteria drive flood-risk priority\nin two mountain catchments — Zimbabwe vs Peru",
            ha="center", va="center", fontsize=11.5, fontweight="bold", color="white")

    steps = [
        ("1. Inputs", "DEM, rainfall, sediment factors, land use/ASM, ES, roads"),
        ("2. Grid prep", "clip to boundary; use common CRS/grid; check NoData"),
        ("3. Criteria", "standardize each layer to 0-1 with direction"),
        ("4. Scenarios", "combine criteria with candidate weights and sensitivity runs"),
        ("5. Outputs", "priority map, top-20% selection frequency, dominant-PIM-criterion map"),
        ("6. Review", "mentor checks criteria, data gaps, and final study site"),
    ]
    x, width, height = 0.09, 0.82, 0.105
    top = 0.82
    gap = 0.035
    positions = [(x, top - i * (height + gap)) for i in range(len(steps))]
    for i, (title, body) in enumerate(steps):
        x, y = positions[i]
        ax.add_patch(Rectangle((x, y), width, height, facecolor="#F7F7F5", edgecolor="0.75", linewidth=1.0))
        ax.add_patch(Rectangle((x, y), 0.008, height, facecolor="#2A9D8F", edgecolor="none"))
        ax.text(x + 0.025, y + height * 0.67, title, fontsize=12.5, fontweight="bold", ha="left", va="center")
        ax.text(x + 0.025, y + height * 0.32, body, fontsize=10.2, ha="left", va="center")
        if i < len(steps) - 1:
            start_xy = (x + width / 2, y)
            end_xy = (x + width / 2, y - gap)
            ax.annotate("", xy=end_xy, xytext=start_xy,
                    arrowprops={"arrowstyle": "->", "linewidth": 1.4, "color": "0.35"})

    ax.text(0.09, 0.035, "Status: prototype / sensitivity scenario. These maps explain PIM criterion drivers; they are not final flood-risk maps.",
            fontsize=10, color="0.25")
    fig.savefig(OUT_DIR / "data_analysis_process_for_boss.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT_DIR / "data_analysis_process_for_boss.pdf", dpi=300, bbox_inches="tight")
    plt.close(fig)


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


def write_text_outputs(manifest_rows: list[dict[str, object]], products_by_site: list[dict[str, object]]) -> None:
    captions = """# Captions: Prototype Priority Criteria Explanation Package

Fig. 1. Colour-coded dominant priority-driver map. Each pixel is coloured by the PIM main criterion that contributes the largest share to the prototype priority score under the current sensitivity scenarios. The map is meant to make the current PIM implementation visually clear; it is not a final flood-risk map.

Fig. 2. Zimbabwe contribution share maps. Each panel shows where one PIM main criterion contributes more strongly to the current prototype priority score. Values are contribution shares, not independent risk probabilities.

Fig. 3. Peru contribution share maps. Each panel shows the same PIM-criterion contribution-share logic for the southern Peru comparison catchment in Arequipa Region, mainly the Vitor-La Joya-Santa Rita de Siguas area west of Arequipa city. It is not a final Peru study-area claim.

Fig. 4. Data analysis process for a concise review briefing. The workflow runs from input data through grid preparation, criterion standardization, sensitivity scenarios, map outputs, and mentor review.
"""
    (OUT_DIR / "mentor_boss_priority_explanation_captions.md").write_text(captions, encoding="utf-8")
    (OUT_DIR / "mentor_boss_priority_explanation_captions.txt").write_text(captions.replace("# Captions: ", ""), encoding="utf-8")

    dominant_lines = []
    for products in products_by_site:
        site: Site = products["site"]  # type: ignore[assignment]
        rows = [row for row in manifest_rows if row["site"] == site.short_label]
        top = sorted(rows, key=lambda r: float(r["dominant_pixel_share"]), reverse=True)[:2]
        dominant_lines.append(
            f"- {site.short_label}: most pixels are driven by {top[0]['criterion_label']} "
            f"({float(top[0]['dominant_pixel_share']) * 100:.1f}%), then {top[1]['criterion_label']} "
            f"({float(top[1]['dominant_pixel_share']) * 100:.1f}%)."
        )
    handoff = f"""# Prototype Priority Criteria Explanation Package

Date: 2026-07-01

Status: `mentor_review_ready` explanation package for prototype / sensitivity-scenario maps.

## What changed

Mentor asked for clearer colour coding on the maps. This package adds a pixel-level dominant
PIM-criterion map and separate contribution-share maps, so the viewer can see why an area
receives a high priority score.

## How to read it

- Dominant criterion map: one colour per PIM main criterion.
- Contribution maps: one panel per scored layer; brighter means that layer contributes a larger
  share of the current priority score in that location.
- Process figure: short presentation-friendly data-analysis workflow.

## Current reading

{chr(10).join(dominant_lines)}

This dominant-colour result is also a diagnostic check. If one implementation layer dominates too
much, that does not mean the model is final; it points to the layer weighting or standardization that
mentor should review first.

## Claim boundary

These are prototype explanation maps. They explain the current PIM criteria and sensitivity-scenario
outputs. They are not final flood-risk maps, not validated intervention-priority maps, and not final
country-comparison claims.

## Files

- `dominant_priority_criterion_maps.png` / `.pdf`
- `zimbabwe_criteria_contribution_maps.png` / `.pdf`
- `peru_criteria_contribution_maps.png` / `.pdf`
- `data_analysis_process_for_boss.png` / `.pdf`
- `priority_criteria_colour_manifest.csv`
- `mentor_boss_priority_explanation_captions.md` / `.txt`
"""
    (OUT_DIR / "mentor_boss_priority_explanation_handoff.md").write_text(handoff, encoding="utf-8")

    message = """Hi Supervisor, I prepared a clearer colour-coded version for the maps.

Now each pixel shows which PIM criterion is driving the priority score most.
I also made separate contribution maps for each PIM criterion, plus a simple data-analysis process figure.

This should be easier to explain in a short presentation:
data inputs -> grid preparation -> 0-1 criteria -> scenario weights -> priority maps -> mentor review.

One useful finding is that the dominant criterion differs between the two prototype sites. I think this is exactly the kind of thing we should review before treating the maps as results.

I kept the wording as prototype / sensitivity scenario, not final flood-risk.
"""
    (OUT_DIR / "mentor_teams_message_draft.txt").write_text(message, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    products_by_site = []
    manifest_rows = []
    for site in SITES:
        products, rows = build_site_products(site)
        products_by_site.append(products)
        manifest_rows.extend(rows)
    write_csv(OUT_DIR / "priority_criteria_colour_manifest.csv", manifest_rows)
    plot_dominant(products_by_site)
    for products in products_by_site:
        plot_contributions(products)
    plot_process()
    write_text_outputs(manifest_rows, products_by_site)
    print(f"Wrote prototype priority explanation package to {OUT_DIR}")


if __name__ == "__main__":
    main()
