#!/usr/bin/env python3
"""Build a Zimbabwe/Peru prototype comparison evidence pack.

The pack compares existing outputs only. It does not rerun criteria generation,
download data, or make final flood-risk claims.
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
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable


ROOT = Path(__file__).resolve().parents[2]
INPUTS = [ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/hotspot_stability_summary.csv", ROOT / "outputs/boundary_v1/criteria_stack_v0_2/revised_criteria_manifest.csv", ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg", ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/hotspot_stability_summary.csv", ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria_stack_manifest.csv", ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"]
OUTPUTS = [ROOT / "outputs/zimbabwe_peru_prototype_comparison/zimbabwe_peru_prototype_comparison_board.png", ROOT / "outputs/zimbabwe_peru_prototype_comparison/zimbabwe_peru_comparison_handoff.md"]
OUT_DIR = ROOT / "outputs/zimbabwe_peru_prototype_comparison"


@dataclass(frozen=True)
class Site:
    label: str
    site_id: str
    boundary_id: str
    experiment_id: str
    claim_level: str
    priority_mean: Path
    top20_frequency: Path
    hotspot_summary: Path
    criteria_manifest: Path
    boundary_gpkg: Path
    boundary_layer: str
    crs_label: str
    status_note: str
    active_criteria_note: str


SITES = [
    Site(
        label="Zimbabwe",
        site_id="zimbabwe_boundary_v1",
        boundary_id="boundary_v1",
        experiment_id="rainfall_exposure_v0_4",
        claim_level="sensitivity_scenario",
        priority_mean=ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/priority_mean.tif",
        top20_frequency=ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/top20_frequency.tif",
        hotspot_summary=ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/hotspot_stability_summary.csv",
        criteria_manifest=ROOT / "outputs/boundary_v1/criteria_stack_v0_2/revised_criteria_manifest.csv",
        boundary_gpkg=ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg",
        boundary_layer="v1_working_boundary",
        crs_label="EPSG:32735",
        status_note="controlled prototype boundary, not final thesis boundary",
        active_criteria_note="displayed v0.4 run uses 6 active criteria, including exposure and rainfall",
    ),
    Site(
        label="Peru",
        site_id="peru_pe1",
        boundary_id="PE1",
        experiment_id="priority_scenarios",
        claim_level="engineering_pilot / sensitivity_scenario",
        priority_mean=ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/priority_mean.tif",
        top20_frequency=ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/top20_frequency.tif",
        hotspot_summary=ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/hotspot_stability_summary.csv",
        criteria_manifest=ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria_stack_manifest.csv",
        boundary_gpkg=ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
        boundary_layer="peru_pilot_boundary",
        crs_label="EPSG:32718",
        status_note="engineering-pilot site, replace if mentor names a Peru site",
        active_criteria_note="displayed PE1 priority run uses 6 active criteria, including exposure and rainfall",
    ),
]


CRITERIA_FIELDS = [
    "site",
    "boundary_id",
    "criterion_family",
    "criterion_name",
    "source_basis",
    "claim_level",
    "limitation",
]

CRITERIA_SPECS = [
    ("Zimbabwe", "boundary_v1", "flood", "flood_hazard_proxy",
     "terrain wetness / drainage proxy from local DEM derivatives", "provisional",
     "susceptibility proxy, not hydraulic inundation depth"),
    ("Zimbabwe", "boundary_v1", "sediment", "sediment_risk_lowR_provisional",
     "K x LS x C structure with provisional low-range R scenario", "provisional",
     "not a final accepted R-factor product"),
    ("Zimbabwe", "boundary_v1", "land use", "land_cover_pressure",
     "WorldCover / C-factor style land-cover pressure", "provisional",
     "land-cover pressure only, not observed damage"),
    ("Zimbabwe", "boundary_v1", "mining", "mining_pressure",
     "OSM / proxy mining and quarry evidence", "diagnostic_only",
     "needs official Zimbabwe mining / ASM evidence"),
    ("Zimbabwe", "boundary_v1", "exposure", "road_accessibility_proxy",
     "OSM road proximity / access-exposure proxy", "diagnostic_only",
     "proxy only, not observed flood impact or vulnerability"),
    ("Zimbabwe", "boundary_v1", "rainfall", "rainfall_climatology_proxy",
     "CHIRPS v3 Africa rainy-season climatology, coarse-to-grid", "sensitivity_scenario",
     "effective resolution about 5 km, not native 30 m rainfall"),
    ("Peru", "PE1", "flood", "flood_hazard_proxy",
     "terrain wetness / drainage proxy from PE1 DEM derivatives", "provisional",
     "engineering-pilot susceptibility proxy"),
    ("Peru", "PE1", "sediment", "erosion_structure_proxy",
     "K x LS x C structure on PE1 reference grid", "diagnostic_only",
     "R-invariant structure, not final soil-loss rate"),
    ("Peru", "PE1", "land use", "land_cover_pressure",
     "WorldCover / C-factor style land-cover pressure", "provisional",
     "arid land cover dominates; interpretation needs site context"),
    ("Peru", "PE1", "mining", "mining_pressure",
     "INGEMMET official small-mining point proximity", "provisional",
     "point proximity, not full active footprint"),
    ("Peru", "PE1", "exposure", "socioeconomic_exposure",
     "OSM road proximity / access-exposure proxy", "provisional",
     "proxy only, not observed flood impact or vulnerability"),
    ("Peru", "PE1", "rainfall", "rainfall_climatology_proxy",
     "CHIRPS v3 LatAm Dec-Mar climatology, coarse-to-grid", "sensitivity_scenario",
     "effective resolution about 5 km, not native 30 m rainfall"),
]


def criteria_rows() -> list[dict[str, object]]:
    return [dict(zip(CRITERIA_FIELDS, row, strict=True)) for row in CRITERIA_SPECS]


def read_metric_csv(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["metric"]: row["value"] for row in csv.DictReader(handle)}


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


def read_raster(path: Path) -> tuple[np.ndarray, dict, tuple[float, float, float, float]]:
    with rasterio.open(path) as src:
        data = src.read(1).astype("float32")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
        data[~np.isfinite(data)] = np.nan
        bounds = rasterio.transform.array_bounds(src.height, src.width, src.transform)
        extent_m = (bounds[0], bounds[2], bounds[1], bounds[3])
        profile = {
            "crs": src.crs,
            "transform": src.transform,
            "width": src.width,
            "height": src.height,
        }
    return data, profile, extent_m


def boundary_area_km2(site: Site, crs) -> float:
    boundary = gpd.read_file(site.boundary_gpkg, layer=site.boundary_layer).to_crs(crs)
    return float(boundary.geometry.area.sum() / 1_000_000)


def valid_summary(data: np.ndarray) -> dict[str, float | int]:
    values = data[np.isfinite(data)]
    return {
        "valid_cells": int(values.size),
        "min": round(float(values.min()), 6),
        "mean": round(float(values.mean()), 6),
        "p80": round(float(np.percentile(values, 80)), 6),
        "p95": round(float(np.percentile(values, 95)), 6),
        "max": round(float(values.max()), 6),
    }


def add_colorbar(fig, ax, image, label: str) -> None:
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.08)
    cb = fig.colorbar(image, cax=cax)
    cb.ax.tick_params(labelsize=8)
    cb.set_label(label, fontsize=9)


def plot_panel(fig, ax, site: Site, raster_path: Path, title: str, cmap: str, label: str) -> None:
    data, profile, extent = read_raster(raster_path)
    image = ax.imshow(np.ma.masked_invalid(data), extent=extent, origin="upper", cmap=cmap, vmin=0, vmax=1)
    boundary = gpd.read_file(site.boundary_gpkg, layer=site.boundary_layer).to_crs(profile["crs"])
    boundary.boundary.plot(ax=ax, color="black", linewidth=0.8)
    ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
    ax.set_xlabel(f"Easting (km, {site.crs_label})", fontsize=9)
    ax.set_ylabel("Northing (km)", fontsize=9)
    km_formatter = FuncFormatter(lambda value, _: f"{value / 1000:.0f}")
    ax.xaxis.set_major_formatter(km_formatter)
    ax.yaxis.set_major_formatter(km_formatter)
    ax.tick_params(labelsize=8)
    ax.grid(color="0.9", linewidth=0.35)
    add_colorbar(fig, ax, image, label)


def build_summary_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for site in SITES:
        metrics = read_metric_csv(site.hotspot_summary)
        priority, profile, _ = read_raster(site.priority_mean)
        top20, _, _ = read_raster(site.top20_frequency)
        stats = valid_summary(priority)
        area = boundary_area_km2(site, profile["crs"])
        stable_area = float(metrics.get("top20_all_scenarios_area_km2", metrics.get("stable_area_km2", "nan")))
        any_area = float(metrics.get("top20_any_scenario_area_km2", metrics.get("any_area_km2", "nan")))
        rows.append({
            "site": site.label,
            "boundary_id": site.boundary_id,
            "experiment_id": site.experiment_id,
            "claim_level": site.claim_level,
            "boundary_area_km2": round(area, 3),
            "criteria_count": metrics.get("criteria_count", "5"),
            "stable_top20_area_km2": round(stable_area, 3),
            "any_top20_area_km2": round(any_area, 3),
            "stable_top20_share_of_boundary": round(stable_area / area, 4),
            "priority_mean": stats["mean"],
            "priority_p80": stats["p80"],
            "priority_p95": stats["p95"],
            "hotspot_frequency_mean": valid_summary(top20)["mean"],
            "status_note": site.status_note,
            "active_criteria_note": site.active_criteria_note,
        })
    return rows


def plot_board() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 10), constrained_layout=True)
    plot_panel(
        fig,
        axes[0, 0],
        SITES[0],
        SITES[0].priority_mean,
        "A. Zimbabwe Upper Mzingwane: mean priority",
        "YlOrRd",
        "0-1 priority",
    )
    plot_panel(
        fig,
        axes[0, 1],
        SITES[1],
        SITES[1].priority_mean,
        "B. Peru pilot site: mean priority",
        "YlOrRd",
        "0-1 priority",
    )
    plot_panel(
        fig,
        axes[1, 0],
        SITES[0],
        SITES[0].top20_frequency,
        "C. Zimbabwe Upper Mzingwane: hotspot frequency",
        "Blues",
        "top-20% frequency",
    )
    plot_panel(
        fig,
        axes[1, 1],
        SITES[1],
        SITES[1].top20_frequency,
        "D. Peru pilot site: hotspot frequency",
        "Blues",
        "top-20% frequency",
    )
    fig.suptitle(
        "Prototype comparison: Zimbabwe and Peru pilot",
        fontsize=14,
        fontweight="bold",
    )
    fig.savefig(OUT_DIR / "zimbabwe_peru_prototype_comparison_board.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT_DIR / "zimbabwe_peru_prototype_comparison_board.pdf", bbox_inches="tight")
    plt.close(fig)


def write_handoff(summary_rows: list[dict[str, object]]) -> None:
    zimbabwe, peru = summary_rows
    handoff = f"""# Zimbabwe-Peru Prototype Comparison Pack

Date: 2026-06-30

Status: `mentor_review_ready` evidence packet for prototype discussion.

This package compares the current Zimbabwe controlled prototype (`boundary_v1`) with the current
Peru engineering pilot (`PE1`). It is not a final flood-risk map, not an intervention-priority
claim, and not a final Zimbabwe-Peru thesis comparison.

## Main reading

- Zimbabwe `boundary_v1` has a six-criteria rainfall + exposure run with a stable top-20% hotspot area of
  {zimbabwe['stable_top20_area_km2']} km2.
- Peru `PE1` has a six-criteria engineering-pilot stack with a stable top-20% hotspot area of
  {peru['stable_top20_area_km2']} km2.
- Both displayed runs now use six active criteria: flood, sediment/erosion structure, land cover,
  mining, exposure/access, and rainfall.
- This is a 6-vs-6 prototype workflow comparison, not a final scientific country comparison.
- The method is now executable on both countries, but the evidence quality is not equal:
  Peru has official INGEMMET mining points, while Zimbabwe still needs stronger official mining or
  ASM data.

## Files

- `zimbabwe_peru_prototype_comparison_board.png` / `.pdf`: four-panel map comparison.
- `zimbabwe_peru_summary.csv`: boundary, scenario, and hotspot summary.
- `zimbabwe_peru_criteria_source_table.csv`: criteria families, data sources, claim levels, and
  limitations.

## Mentor question

Can I use `boundary_v1` and `PE1` as prototype sites for the comparative pipeline, while keeping the
final study sites and final claims open?

## Data to request during the trip

1. Zimbabwe official mining / ASM footprints or active-site points.
2. Observed flood-impact or damaged-road / affected-settlement evidence.
3. Confirmation whether PE1 is acceptable as a Peru pilot, or whether a different Peru site should
   replace it.
4. Any local rainfall station or high-frequency rainfall data that can support the R-factor range.
"""
    (OUT_DIR / "zimbabwe_peru_comparison_handoff.md").write_text(handoff, encoding="utf-8")

    caption = (
        "Fig. X. Prototype comparison between the Upper Mzingwane prototype catchment "
        "in Zimbabwe and the current Peru pilot catchment. "
        "Both displayed maps use six active criteria. "
        "The upper panels show mean priority across sensitivity scenarios; the lower panels show "
        "how often each cell appears in the top-20% hotspot set. The figure is for mentor review "
        "of the prototype pipeline only. It is not a validated flood-risk map or a final "
        "Zimbabwe-Peru comparison."
    )
    (OUT_DIR / "zimbabwe_peru_comparison_caption.txt").write_text(caption + "\n", encoding="utf-8")
    (OUT_DIR / "zimbabwe_peru_comparison_caption.md").write_text(
        "# Caption\n\n" + caption + "\n",
        encoding="utf-8",
    )

    mentor_message = """Hi Supervisor, I moved the work forward into a simple Zimbabwe-Peru prototype comparison.

For Zimbabwe, I used the Upper Mzingwane prototype catchment.
For Peru, I used a temporary pilot catchment, only to test whether the same workflow runs there.

The method now runs on both sides with six active criteria:
flood, sediment/erosion structure, land cover, mining, exposure/access, and rainfall.

The important difference is data quality: Peru has official mining points, but Zimbabwe still needs better mining / ASM data.

My question before your trip is simple:
Can I keep using these two sites as prototype sites for now, while we keep the final study sites open?
"""
    (OUT_DIR / "zimbabwe_peru_mentor_message_draft.txt").write_text(mentor_message, encoding="utf-8")
    (OUT_DIR / "zimbabwe_peru_mentor_message_draft.md").write_text(mentor_message, encoding="utf-8")


def ensure_inputs() -> None:
    paths = []
    for site in SITES:
        paths.extend([
            site.priority_mean,
            site.top20_frequency,
            site.hotspot_summary,
            site.criteria_manifest,
            site.boundary_gpkg,
        ])
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required inputs:\n" + "\n".join(missing))


def main() -> None:
    ensure_inputs()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_rows = build_summary_rows()
    write_csv(OUT_DIR / "zimbabwe_peru_summary.csv", summary_rows)
    write_csv(OUT_DIR / "zimbabwe_peru_criteria_source_table.csv", criteria_rows())
    plot_board()
    write_handoff(summary_rows)
    print(f"Wrote comparison pack to {OUT_DIR}")


if __name__ == "__main__":
    main()
