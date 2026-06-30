#!/usr/bin/env python3
"""Diagnose spatial agreement between boundary_v1 hotspots and exposure evidence.

IFPM-089 hardening task: do the v0.2 stable hotspots fall where real exposure
evidence exists (road-river crossings, settlements, mining pressure, population)?
This is a DIAGNOSTIC of spatial co-location, NOT validation. It does not claim
the hotspots are validated flood risk.

Inputs (all confirmed to exist):
  - v0.2 hotspot rasters (priority_mean, top20_frequency) on the V1 grid.
  - Vector points from v1_full_methodology_review_layers.gpkg:
      road_river_crossings_v1 (64), osm_places_v1 (8).
  - Mining proximity raster (already grid-aligned to V1).
  - Native-grid population rasters (WorldPop, GHSL): summarised by ZONAL
    aggregation over the V1 boundary, NOT resampled to 30 m (avoid false
    30 m precision, per candidate_data_upgrade_matrix rules).

Output claim level: `diagnostic_only`.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from mpl_toolkits.axes_grid1 import make_axes_locatable
from rasterio.features import geometry_mask
from rasterio.mask import mask


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY_ID = "boundary_v1"
EXPERIMENT_ID = "hotspot_exposure_diagnostic_v0_3"
OUT_DIR = ROOT / f"outputs/{BOUNDARY_ID}/{EXPERIMENT_ID}"

# Inputs from the main workspace outputs/. Default to ROOT/outputs (correct in
# the main checkout); set IFPM_MAIN_OUTPUTS to run inside a worktree.
MAIN_OUTPUTS = Path(os.environ.get("IFPM_MAIN_OUTPUTS", ROOT / "outputs"))
REF = MAIN_OUTPUTS / "srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif"
V1_GPKG = MAIN_OUTPUTS / "v1_working_boundary/v1_working_boundary.gpkg"
V02_BASELINE = MAIN_OUTPUTS / f"{BOUNDARY_ID}/priority_scenarios_v0_2"
EVIDENCE_GPKG = MAIN_OUTPUTS / "v1_full_methodology_evidence_sweep/v1_full_methodology_review_layers.gpkg"
MINING_PROX_RASTER = MAIN_OUTPUTS / "v1_full_methodology_evidence_sweep/rasters/v1_closeness_to_mining_proxy_0_1_utm35s_30m.tif"
WORLDPOP_RASTER = MAIN_OUTPUTS / "v1_full_methodology_evidence_sweep/rasters/v1_worldpop_2020_unadj_native.tif"
GHSL_BUILT_RASTER = MAIN_OUTPUTS / "v1_full_methodology_evidence_sweep/rasters/v1_ghsl_built_surface_2025_native.tif"

CELL_AREA_KM2 = 0.0009
# Stable hotspot = appears in >=2 of 3 v0.2 scenarios.
STABLE_FREQ_THRESHOLD = 0.667


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


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


def read_reference() -> dict:
    with rasterio.open(REF) as ref:
        return ref.profile.copy()


def read_band(path: Path, profile: dict) -> np.ndarray:
    with rasterio.open(path) as src:
        data = src.read(1).astype("float32")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
    data[~np.isfinite(data)] = np.nan
    return data


def v1_inside_mask(profile: dict) -> np.ndarray:
    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(profile["crs"])
    return geometry_mask(
        [boundary.geometry.iloc[0].__geo_interface__],
        out_shape=(profile["height"], profile["width"]),
        transform=profile["transform"],
        invert=True,
    )


def points_in_hotspot_bands(
    points: gpd.GeoDataFrame, freq: np.ndarray, profile: dict, inside: np.ndarray, label: str
) -> list[dict[str, object]]:
    """Sample hotspot frequency at each point and tally by band.

    Buckets keep "outside V1" and "NoData inside V1" separate for honesty: a
    point inside the boundary that lands on a NoData cell is NOT the same as a
    point outside the boundary, even though for this run the v0.2 freq raster is
    fully valid inside V1 so the NoData bucket is expected to be empty.
    """
    pts = points.to_crs(profile["crs"])
    rows, cols = rasterio.transform.rowcol(profile["transform"], pts.geometry.x.values, pts.geometry.y.values)
    bands = {
        "low (freq<0.333)": 0,
        "medium (0.333-0.667)": 0,
        "high (>=0.667 stable)": 0,
        "outside_v1": 0,
        "no_data_inside_v1": 0,
    }
    for r, c in zip(rows, cols):
        if not (0 <= r < profile["height"] and 0 <= c < profile["width"]):
            bands["outside_v1"] += 1
            continue
        if not inside[r, c]:
            bands["outside_v1"] += 1
            continue
        if not np.isfinite(freq[r, c]):
            bands["no_data_inside_v1"] += 1
            continue
        val = float(freq[r, c])
        if val >= STABLE_FREQ_THRESHOLD:
            bands["high (>=0.667 stable)"] += 1
        elif val >= 0.333:
            bands["medium (0.333-0.667)"] += 1
        else:
            bands["low (freq<0.333)"] += 1
    total = int(sum(bands.values()))
    return [
        {"evidence": label, "band": band, "count": cnt, "share": round(cnt / total, 4) if total else 0.0}
        for band, cnt in bands.items()
    ]


def zonal_population_by_hotspot(
    pop_raster: Path, freq: np.ndarray, profile: dict, inside: np.ndarray, label: str
) -> dict[str, object]:
    """Zonal-sum a native-grid population raster over V1, split by stable-hotspot
    vs non-hotspot. Population is NOT resampled to 30 m; it is masked to the V1
    boundary on its native grid and the per-cell hotspot band (upsampled by
    nearest label for zonal assignment only) is used to split the sum.

    To avoid false precision, population stays on its native grid; only the
    stable-hotspot LABEL is nearest-assigned to native cells for grouping.
    """
    from rasterio.warp import reproject, Resampling

    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary")
    with rasterio.open(pop_raster) as src:
        # Reproject boundary into the population raster's own CRS (WorldPop is
        # EPSG:4326, GHSL is ESRI:54009 Mollweide) so the mask overlaps.
        boundary = boundary.to_crs(src.crs)
        # IMPORTANT: mask(crop=True) returns (cropped_array, cropped_transform).
        # The cropped transform is the origin of the cropped window and MUST be
        # reused as the reproject destination transform, otherwise the label
        # band is placed at the wrong origin relative to the population array.
        data, out_transform = mask(
            src, [boundary.geometry.iloc[0].__geo_interface__], crop=True, filled=True, nodata=src.nodata
        )
        arr = data[0].astype("float64")
        if src.nodata is not None:
            arr[arr == src.nodata] = np.nan
        # Upsample the stable-hotspot label to the CROPPED native pop grid via
        # reproject (nearest). Only the boolean label is resampled, never the
        # population. dst_transform MUST be the cropped out_transform.
        label_band = np.where(inside & np.isfinite(freq) & (freq >= STABLE_FREQ_THRESHOLD), 1, 0).astype("float32")
        native_label = np.full(arr.shape, np.nan, dtype="float32")
        reproject(
            source=label_band,
            destination=native_label,
            src_transform=profile["transform"],
            src_crs=profile["crs"],
            dst_transform=out_transform,
            dst_crs=src.crs,
            resampling=Resampling.nearest,
        )
        hot = (native_label >= 0.5) & np.isfinite(arr)
        cold = (native_label < 0.5) & np.isfinite(arr)
        hot_sum = float(np.nansum(arr[hot]))
        cold_sum = float(np.nansum(arr[cold]))
        hot_cells = int(np.sum(hot))
        cold_cells = int(np.sum(cold))
        native_crs_str = str(src.crs)
        native_res_str = f"{src.res[0]:g} x {src.res[1]:g}"
    total = hot_sum + cold_sum
    return {
        "evidence": label,
        "native_crs": native_crs_str,
        "native_resolution": native_res_str,
        "stable_hotspot_pop_sum": round(hot_sum, 1),
        "non_hotspot_pop_sum": round(cold_sum, 1),
        "total_pop_sum": round(total, 1),
        "share_in_stable_hotspot": round(hot_sum / total, 4) if total else 0.0,
        "stable_hotspot_native_cells": hot_cells,
        "non_hotspot_native_cells": cold_cells,
        "method": "zonal sum on native grid; only the stable-hotspot label is nearest-resampled for grouping (population NOT resampled to 30 m)",
    }


def plot_board(freq: np.ndarray, inside: np.ndarray, profile: dict) -> None:
    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(profile["crs"])
    crossings = gpd.read_file(EVIDENCE_GPKG, layer="road_river_crossings_v1").to_crs(profile["crs"])
    places = gpd.read_file(EVIDENCE_GPKG, layer="osm_places_v1").to_crs(profile["crs"])
    bounds = rasterio.transform.array_bounds(profile["height"], profile["width"], profile["transform"])
    extent = (bounds[0] / 1000, bounds[2] / 1000, bounds[1] / 1000, bounds[3] / 1000)

    fig, ax = plt.subplots(figsize=(8.5, 7), constrained_layout=True)
    masked = np.ma.masked_invalid(freq)
    masked[~inside] = np.ma.masked
    im = ax.imshow(masked, extent=extent, origin="upper", cmap="YlOrRd", vmin=0, vmax=1)
    boundary.boundary.plot(ax=ax, color="black", linewidth=1.0)
    crossings.plot(ax=ax, marker="o", color="blue", markersize=14, label="road-river crossings (64)", edgecolor="white", linewidth=0.3)
    places.plot(ax=ax, marker="^", color="lime", markersize=46, label="OSM places (8)", edgecolor="black", linewidth=0.5)
    ax.set_title("boundary_v1 v0.2 hotspot frequency vs exposure points", loc="left", fontsize=11, fontweight="bold")
    ax.set_xlabel("Easting (km, EPSG:32735)", fontsize=9)
    ax.set_ylabel("Northing (km)", fontsize=9)
    ax.legend(loc="lower left", fontsize=8, framealpha=0.9)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.04)
    cb = fig.colorbar(im, cax=cax)
    cb.set_label("v0.2 top-20% frequency (stable >= 0.667)", fontsize=8)
    fig.savefig(OUT_DIR / "hotspot_exposure_board.png", dpi=220, bbox_inches="tight")
    fig.savefig(OUT_DIR / "hotspot_exposure_board.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    profile = read_reference()
    inside = v1_inside_mask(profile)

    freq = read_band(V02_BASELINE / "top20_frequency.tif", profile)
    priority_mean = read_band(V02_BASELINE / "priority_mean.tif", profile)

    stable = inside & np.isfinite(freq) & (freq >= STABLE_FREQ_THRESHOLD)
    stable_cells = int(np.sum(stable))
    stable_area = stable_cells * CELL_AREA_KM2

    summary_rows: list[dict[str, object]] = [
        {"metric": "claim_level", "value": "diagnostic_only"},
        {"metric": "stable_hotspot_threshold", "value": f"top20_frequency >= {STABLE_FREQ_THRESHOLD}"},
        {"metric": "stable_hotspot_cells", "value": stable_cells},
        {"metric": "stable_hotspot_area_km2", "value": round(stable_area, 3)},
    ]

    # --- Point evidence: crossings and places ---
    crossings = gpd.read_file(EVIDENCE_GPKG, layer="road_river_crossings_v1")
    places = gpd.read_file(EVIDENCE_GPKG, layer="osm_places_v1")
    point_rows = points_in_hotspot_bands(crossings, freq, profile, inside, "road_river_crossings")
    point_rows += points_in_hotspot_bands(places, freq, profile, inside, "osm_places")

    # --- Raster evidence: mining proximity (grid-aligned) Pearson r ---
    mining = read_band(MINING_PROX_RASTER, profile)
    valid = inside & np.isfinite(priority_mean) & np.isfinite(mining)
    a = priority_mean[valid]
    b = mining[valid]
    if a.size > 1:
        r_matrix = np.corrcoef(a, b)
        pearson_r = float(r_matrix[0, 1])
    else:
        pearson_r = float("nan")
    # Mean mining pressure inside stable hotspots vs elsewhere.
    mining_in_stable = float(np.nanmean(mining[stable])) if np.isfinite(mining[stable]).any() else float("nan")
    mining_in_rest = inside & np.isfinite(mining) & ~stable
    mining_in_rest_mean = float(np.nanmean(mining[mining_in_rest])) if mining_in_rest.any() else float("nan")

    raster_rows = [
        {"evidence": "mining_proximity_proxy", "comparison": "pearson_r_priority_vs_mining", "value": round(pearson_r, 6)},
        {"evidence": "mining_proximity_proxy", "comparison": "mean_mining_in_stable_hotspot", "value": round(mining_in_stable, 6)},
        {"evidence": "mining_proximity_proxy", "comparison": "mean_mining_in_non_hotspot", "value": round(mining_in_rest_mean, 6)},
    ]

    # --- Population zonal summaries (native grid, not resampled) ---
    pop_rows: list[dict[str, object]] = []
    for pop_path, pop_label in [(WORLDPOP_RASTER, "worldpop_2020"), (GHSL_BUILT_RASTER, "ghsl_built_surface_2025")]:
        if pop_path.exists():
            pop_rows.append(zonal_population_by_hotspot(pop_path, freq, profile, inside, pop_label))

    plot_board(freq, inside, profile)

    write_csv(OUT_DIR / "hotspot_exposure_summary.csv", summary_rows)
    write_csv(OUT_DIR / "point_evidence_by_hotspot_band.csv", point_rows)
    write_csv(OUT_DIR / "raster_evidence_correlation.csv", raster_rows)
    write_csv(OUT_DIR / "population_zonal_summary.csv", pop_rows)
    print(f"wrote {BOUNDARY_ID} / {EXPERIMENT_ID} to {rel(OUT_DIR)}")
    print(f"stable hotspot: {stable_cells} cells ({stable_area:.1f} km^2)")
    print(f"mining-proximity Pearson r vs priority_mean: {pearson_r:.4f}")
    for row in point_rows:
        if "high" in str(row["band"]):
            print(f"  {row['evidence']} in high/stable band: {row['count']} ({row['share']:.1%})")


if __name__ == "__main__":
    main()
