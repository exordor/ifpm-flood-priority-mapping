#!/usr/bin/env python3
"""Build a Zimbabwe/Peru prototype comparison evidence pack.

The pack compares existing outputs only. It does not rerun criteria generation,
download data, or make final flood-risk claims.
"""

from __future__ import annotations

import csv
import sys
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
sys.path.insert(0, str(ROOT / "bin/package"))
from write_zimbabwe_peru_source_tables import write_source_tables

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
        status_note="Upper Mzingwane catchment (~3689 km², semi-arid); prototype boundary, not final thesis boundary",
        active_criteria_note="mentor 5-main-criterion framework; current run uses 6 scored implementation layers",
    ),
    Site(
        label="Peru",
        site_id="peru_southern_comparison_catchment",
        boundary_id="PE1",
        experiment_id="priority_scenarios",
        claim_level="provisional / sensitivity_scenario",
        priority_mean=ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/priority_mean.tif",
        top20_frequency=ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/top20_frequency.tif",
        hotspot_summary=ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/hotspot_stability_summary.csv",
        criteria_manifest=ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria_stack_manifest.csv",
        boundary_gpkg=ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
        boundary_layer="peru_pilot_boundary",
        crs_label="EPSG:32718",
        status_note="Arequipa Region, mainly Vitor-La Joya-Santa Rita de Siguas west of Arequipa city; final Peru study area remains open",
        active_criteria_note="mentor 5-main-criterion framework; current run uses 6 scored implementation layers",
    ),
]


CRITERIA_FIELDS = [
    "site",
    "boundary_id",
    "ahp_main_criterion",
    "scored_implementation_layers",
    "source_basis",
    "claim_level",
    "limitation",
]

CRITERIA_SPECS = [
    ("Zimbabwe", "boundary_v1", "Flood (FH)", "flood_conditioning_factors; rainfall_climatology sensitivity layer",
     "DEM-derived TWI / distance-to-drainage plus CHIRPS rainy-season climatology", "provisional / sensitivity_scenario",
     "not hydraulic inundation depth; rainfall is coarse-to-grid context"),
    ("Zimbabwe", "boundary_v1", "Sediment (SR)", "soil_erosion_factors",
     "K x LS x C structure on the V1 reference grid", "diagnostic_only",
     "K x LS x C structure; rainfall erosivity not applied"),
    ("Zimbabwe", "boundary_v1", "Land Use / ASM (LU)", "land_cover_pressure; mining_pressure",
     "WorldCover / C-factor style land-cover pressure plus USGS mineral reference proximity", "provisional",
     "not observed damage; Zimbabwe still needs local ASM mapping"),
    ("Zimbabwe", "boundary_v1", "Environmental (ES)", "not independently scored",
     "No accepted independent environmental-sensitivity raster in the current run", "data_gap",
     "must not be presented as an implemented scored layer"),
    ("Zimbabwe", "boundary_v1", "Socioeconomic (SV)", "exposure_indicators",
     "OSM road proximity / access-exposure indicator", "diagnostic_only",
     "indicator only, not observed flood impact or vulnerability"),
    ("Peru", "PE1", "Flood (FH)", "flood_conditioning_factors; rainfall_climatology sensitivity layer",
     "DEM-derived TWI / distance-to-drainage plus CHIRPS rainy-season climatology", "provisional / sensitivity_scenario",
     "provisional susceptibility indicator; rainfall is coarse-to-grid context"),
    ("Peru", "PE1", "Sediment (SR)", "soil_erosion_factors",
     "K x LS x C structure on PE1 reference grid", "diagnostic_only",
     "K x LS x C structure; rainfall erosivity not applied"),
    ("Peru", "PE1", "Land Use / ASM (LU)", "land_cover_pressure; mining_pressure",
     "WorldCover / C-factor style pressure plus INGEMMET official small-mining point proximity", "provisional",
     "arid land-cover interpretation needs site context; mining is point proximity, not active footprint"),
    ("Peru", "PE1", "Environmental (ES)", "not independently scored",
     "No accepted independent environmental-sensitivity raster in the current run", "data_gap",
     "must not be presented as an implemented scored layer"),
    ("Peru", "PE1", "Socioeconomic (SV)", "exposure_indicators",
     "OSM road proximity / access-exposure indicator", "provisional",
     "indicator only, not observed flood impact or vulnerability"),
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
        ahp_count = metrics.get("ahp_main_criteria_count", "5")
        scored_count = metrics.get("scored_layer_count", "")
        rows.append({
            "site": site.label,
            "boundary_id": site.boundary_id,
            "experiment_id": site.experiment_id,
            "claim_level": site.claim_level,
            "boundary_area_km2": round(area, 3),
            "ahp_main_criteria_count": ahp_count,
            "scored_layer_count": scored_count,
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
        "A. Zimbabwe: mean priority",
        "YlOrRd",
        "0-1 priority",
    )
    plot_panel(
        fig,
        axes[0, 1],
        SITES[1],
        SITES[1].priority_mean,
        "B. Peru: mean priority",
        "YlOrRd",
        "0-1 priority",
    )
    plot_panel(
        fig,
        axes[1, 0],
        SITES[0],
        SITES[0].top20_frequency,
        "C. Zimbabwe: top-20% hotspot frequency",
        "Blues",
        "top-20% frequency",
    )
    plot_panel(
        fig,
        axes[1, 1],
        SITES[1],
        SITES[1].top20_frequency,
        "D. Peru: top-20% hotspot frequency",
        "Blues",
        "top-20% frequency",
    )
    fig.suptitle(
        "Prototype comparison: Zimbabwe and southern Peru",
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

This package compares the current Upper Mzingwane controlled prototype with the southern Peru
comparison catchment in Arequipa Region, mainly the Vitor-La Joya-Santa Rita de Siguas area west of Arequipa city. It is not a final flood-risk map, not an intervention-priority
claim, and not a final Zimbabwe-Peru thesis comparison.

## Main reading

- The Upper Mzingwane prototype follows the mentor 5-main-criterion framework with six scored implementation layers; stable top-20% hotspot area:
  {zimbabwe['stable_top20_area_km2']} km2.
- The southern Peru comparison catchment follows the same 5-main-criterion framework with six scored implementation layers; stable top-20% hotspot area:
  {peru['stable_top20_area_km2']} km2.
- The five AHP main criteria are Flood, Sediment, Land Use / ASM, Environmental, and
  Socioeconomic. The executable overlay currently scores six implementation layers because
  Land Use / ASM is split into land-cover and mining, rainfall is a sensitivity layer, and
  Environmental is not yet an independent scored raster.
- This is a 5-framework / implementation-layer prototype comparison, not a final scientific
  country comparison.
- The method is now executable on both countries, but the evidence quality is not equal:
  Peru has official INGEMMET mining points, while Zimbabwe still needs stronger official mining or
  ASM data.

## Files

- `zimbabwe_peru_prototype_comparison_board.png` / `.pdf`: four-panel map comparison.
- `zimbabwe_peru_summary.csv`: boundary, scenario, and hotspot summary.
- `zimbabwe_peru_criteria_source_table.csv`: AHP main criteria, data sources, claim levels, and
  limitations.

## Mentor question

Can I use Upper Mzingwane and the southern Peru comparison catchment west of Arequipa city to test the
comparative pipeline, while keeping final study-site decisions and final claims open?

## Data to request during the trip

1. Zimbabwe official mining / ASM footprints or active-site points.
2. Observed flood-impact or damaged-road / affected-settlement evidence.
3. Confirmation whether the current southern Peru comparison catchment is acceptable, or whether a different Peru site should
   replace it.
4. Any local rainfall station or high-frequency rainfall data that can support the R-factor range.
"""
    (OUT_DIR / "zimbabwe_peru_comparison_handoff.md").write_text(handoff, encoding="utf-8")

    caption = (
        "Fig. X. Prototype comparison between the Upper Mzingwane prototype catchment "
        "in Zimbabwe and the southern Peru comparison catchment in Arequipa Region, mainly the Vitor-La Joya-Santa Rita de Siguas area west of Arequipa city. "
        "Both displayed maps follow the mentor five-main-criterion AHP framework, while the "
        "current executable overlay uses six scored implementation layers. "
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
For Peru, I used a southern Peru comparison catchment in Arequipa Region, mainly the Vitor-La Joya-Santa Rita de Siguas area west of Arequipa city, to test whether the same workflow runs there.

The method now runs on both sides using the mentor's five main AHP criteria:
Flood, Sediment, Land Use / ASM, Environmental, and Socioeconomic.

The current executable overlay still has six scored implementation layers because Land Use / ASM is split into land-cover and mining, rainfall is tested as a sensitivity layer, and Environmental is not yet an independent scored raster.

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
    write_source_tables(OUT_DIR)
    plot_board()
    write_handoff(summary_rows)
    print(f"Wrote comparison pack to {OUT_DIR}")


if __name__ == "__main__":
    main()
