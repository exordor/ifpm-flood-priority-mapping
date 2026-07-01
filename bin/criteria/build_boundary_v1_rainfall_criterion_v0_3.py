#!/usr/bin/env python3
"""Build a CHIRPS-derived rainfall criterion on the V1 reference grid (v0.3).

This script turns the existing native 0.05 deg CHIRPS `rainy_season_mean_1981_2024`
raster into a V1-reference-grid (EPSG:32735, 30 m) MCDA criterion layer for the
`boundary_v1 / rainfall_sensitivity_v0_3` experiment.

GOVERNANCE (per v1_terrain_reference_grid_rule.md lines 129-138 and AGENTS.md
"Rainfall / CHIRPS" rules): CHIRPS is ~5 km native. This is an explicitly
labelled coarse-to-reference-grid resample, allowed ONLY as a
`sensitivity_scenario` input, never as native 30 m rainfall evidence. The
allowance (rule lines 129-131) is the general CHIRPS coarse-to-reference-grid
clause; the V2 R-factor diagnostic waiver (rule lines 140-160) is cited only as
a precedent for the same labelling convention (explicit suffix + IFPM_NOTE band
tag), not as a transferred waiver:
  - the output carries the explicit `_PROVISIONAL_30m` suffix;
  - the GeoTIFF band carries an `IFPM_NOTE` tag stating it is not pixel-level
    30 m rainfall evidence;
  - the primary rainfall products remain the native 0.05 deg rasters and the
    zonal scalars in chirps_v3_zimbabwe_prototype;
  - this layer must NOT drive any final flood-risk, sediment-risk, or
    intervention-priority claim.

The criterion name is `rainfall_climatology_proxy`, not `rainfall` or
`rainfall_intensity`, to make the proxy nature explicit (AGENTS.md criteria
design rules: names must describe what the data actually measure).
"""

from __future__ import annotations

import csv
import os
from datetime import date
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from rasterio.features import geometry_mask
from rasterio.warp import reproject, Resampling


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY_ID = "boundary_v1"
EXPERIMENT_ID = "rainfall_sensitivity_v0_3"
OUT_DIR = ROOT / f"outputs/{BOUNDARY_ID}/{EXPERIMENT_ID}/criteria"

# Inputs (reference DEM, CHIRPS, V1 boundary) live in the main workspace
# outputs/, which is gitignored and therefore absent in a worktree checkout.
# Default to ROOT/outputs (correct when run in the main checkout). To run inside
# a worktree, set IFPM_MAIN_OUTPUTS to the main checkout's outputs/ directory.
MAIN_OUTPUTS = Path(os.environ.get("IFPM_MAIN_OUTPUTS", ROOT / "outputs"))
REF = MAIN_OUTPUTS / "srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif"
CHIRPS_NATIVE = (
    MAIN_OUTPUTS
    / "chirps_v3_zimbabwe_prototype/rainfall_comparison/rasters/rainy_season_mean_1981_2024.tif"
)
V1_GPKG = MAIN_OUTPUTS / "v1_working_boundary/v1_working_boundary.gpkg"

# Governance metadata (the six required fields, both rule sources agree).
CRITERION_NAME = "rainfall_climatology_proxy"
SOURCE_METRIC = "rainy_season_mean_1981_2024"
SOURCE_UNIT = "mm/season (Nov-Mar climatological mean, 1981/82-2023/24)"
NATIVE_RESOLUTION = "0.05 deg (~5 km) CHIRPS v3.0 Africa"
TARGET_GRID = "V1 reference: EPSG:32735, 30 m, 2712 x 3459 (v1_dem_utm35s_30m.tif)"
RESAMPLING_METHOD = "bilinear"
EFFECTIVE_RESOLUTION_WARNING = (
    "Effective resolution is ~5 km despite 30 m cells; values are smooth "
    "climatological context, NOT pixel-level 30 m rainfall intensity."
)
CLAIM_LEVEL = "sensitivity_scenario"
LINEAGE = (
    "CHIRPS v3.0 Africa rainy-season mean resampled to V1 grid for the "
    "rainfall_sensitivity_v0_3 MCDA overlay test. Native 0.05 deg raster and "
    "zonal scalars remain the primary products."
)
IFPM_NOTE = (
    "SENSITIVITY SCENARIO ONLY: 0.05 deg CHIRPS rainy-season mean resampled to "
    "30 m via bilinear for overlay compatibility. NOT pixel-level 30 m rainfall "
    "evidence. Do not use for final flood-risk or intervention-priority claims."
)


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def read_reference() -> dict:
    with rasterio.open(REF) as ref:
        return ref.profile.copy()


def v1_inside_mask(ref_profile: dict) -> np.ndarray:
    """Boolean mask of cells inside the V1 working boundary, on the reference grid."""
    import geopandas as gpd

    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(ref_profile["crs"])
    if len(boundary) != 1 or boundary.geometry.iloc[0].is_empty:
        raise ValueError("Expected one non-empty V1 working boundary")
    return geometry_mask(
        [boundary.geometry.iloc[0].__geo_interface__],
        out_shape=(ref_profile["height"], ref_profile["width"]),
        transform=ref_profile["transform"],
        invert=True,
    )


def fill_edge_nodata(data: np.ndarray, inside: np.ndarray) -> tuple[np.ndarray, dict[str, int]]:
    """Fill resampling-edge NoData slivers inside V1 (documented imputation).

    The coarse-to-fine bilinear resample leaves saw-tooth NoData along the
    irregular V1 polygon edge because the 0.05 deg source cells do not tile the
    UTM-35S polygon boundary exactly. These holes are resampling GEOMETRY
    artifacts (edge slivers connected to the raster outside, not interior
    holes), not real missing rainfall. They are filled with nearest-valid-value
    extrapolation via a Euclidean distance transform, strictly inside the V1
    boundary and drawing ONLY from inside-V1 valid sources; cells outside V1
    stay NoData. This is a documented imputation per AGENTS.md NoData policy;
    the method and scope are recorded in the manifest.

    Returns (filled_array, stats) where stats reports interior-hole count so the
    caller can record whether any genuine interior gap was silently imputed.
    """
    from scipy.ndimage import label as ndimage_label

    work = data.astype("float64").copy()
    holes = inside & ~np.isfinite(work)
    if not holes.any():
        return work, {"hole_cells": 0, "interior_holes": 0, "edge_sliver_holes": 0}
    # Classify holes: an interior hole is fully surrounded by valid cells inside
    # V1 (a genuine data gap); an edge sliver touches outside-V1 NoData. Only
    # edge slivers are geometry artifacts; interior holes would be real gaps.
    outside = ~inside
    labeled, n = ndimage_label(holes)
    interior = 0
    edge_sliver = 0
    for i in range(1, n + 1):
        region = labeled == i
        dilated = np.zeros_like(region)
        dilated[1:-1, 1:-1] = (
            region[2:, 1:-1] | region[:-2, 1:-1] | region[1:-1, 2:] | region[1:-1, :-2]
            | region[2:, 2:] | region[2:, :-2] | region[:-2, 2:] | region[:-2, :-2]
        )
        if (dilated & outside).any():
            edge_sliver += 1
        else:
            interior += 1
    # Restrict nearest sources to inside-V1 valid cells so outside-V1 CHIRPS
    # values never feed an inside-V1 hole.
    valid_inside = inside & np.isfinite(work)
    _, (row_idx, col_idx) = distance_transform_edt(~valid_inside, return_indices=True)
    filled = work[row_idx, col_idx]
    filled[~inside] = np.nan
    return filled, {
        "hole_cells": int(holes.sum()),
        "interior_holes": interior,
        "edge_sliver_holes": edge_sliver,
    }


def resample_to_reference(src_path: Path, ref_profile: dict) -> np.ndarray:
    """Bilinear-resample a coarse raster onto the V1 reference grid.

    Mirrors derive_v2_usle_soil_loss.py:resample_r_to_30m (lines 110-131).
    Bilinear is used because rainfall is a continuous climatology field; nearest
    would create block artifacts. Result is labelled provisional-only and is not
    pixel-level 30 m evidence.
    """
    dst = np.full((ref_profile["height"], ref_profile["width"]), np.nan, dtype="float64")
    with rasterio.open(src_path) as src:
        reproject(
            source=rasterio.band(src, 1),
            destination=dst,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=ref_profile["transform"],
            dst_crs=ref_profile["crs"],
            resampling=Resampling.bilinear,
            src_nodata=src.nodata,
            dst_nodata=np.nan,
        )
    dst[~np.isfinite(dst)] = np.nan
    return dst


def write_raster(
    path: Path,
    data: np.ndarray,
    profile: dict,
    dtype: str = "float32",
    nodata: float = -9999.0,
    ifpm_note: str = "",
) -> None:
    out_profile = profile.copy()
    out_profile.update(driver="GTiff", count=1, dtype=dtype, nodata=nodata, compress="deflate", tiled=True)
    encoded = np.where(np.isfinite(data), data, nodata).astype(dtype)
    with rasterio.open(path, "w", **out_profile) as dst:
        dst.write(encoded, 1)
        if ifpm_note:
            dst.update_tags(1, IFPM_NOTE=ifpm_note)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ref_profile = read_reference()
    inside = v1_inside_mask(ref_profile)
    inside_total = int(inside.sum())

    raw = resample_to_reference(CHIRPS_NATIVE, ref_profile)
    raw_valid_before = int((inside & np.isfinite(raw)).sum())
    raw_frac_before = raw_valid_before / inside_total if inside_total else 0.0

    # Documented imputation: fill thin resampling-edge NoData slivers inside V1.
    raw, fill_stats = fill_edge_nodata(raw, inside)
    valid = np.isfinite(raw)
    raw_valid_after = int((inside & np.isfinite(raw)).sum())
    raw_frac_after = raw_valid_after / inside_total if inside_total else 0.0
    if not valid.any():
        raise ValueError("resampled rainfall raster has no valid cells")
    if fill_stats["interior_holes"] > 0:
        # A genuine interior gap would be real missing data, not a geometry
        # artifact; do not silently impute it. Surface it so the run is honest.
        raise ValueError(
            f"{fill_stats['interior_holes']} interior hole region(s) found inside V1; "
            "refusing to impute genuine data gaps. Inspect the CHIRPS source coverage."
        )

    raw_min = float(np.nanmin(raw))
    raw_mean = float(np.nanmean(raw))
    raw_max = float(np.nanmax(raw))

    # Max-normalize to [0,1] for MCDA scoring (same convention as the LOW-R
    # sediment criterion in run_boundary_v1_priority_scenarios.py). Monotonic, so
    # the highest-rainfall cell becomes 1.0 and ranking is preserved.
    if raw_max <= 0:
        raise ValueError(f"non-positive rainfall range, max={raw_max}")
    score = (raw / raw_max).astype("float32")
    score = np.clip(score, 0.0, 1.0)
    score[~valid] = np.nan

    raw_path = OUT_DIR / f"{CRITERION_NAME}_raw_mm_per_season_PROVISIONAL_30m.tif"
    score_path = OUT_DIR / f"{CRITERION_NAME}_0_1_PROVISIONAL_30m.tif"
    write_raster(raw_path, raw, ref_profile, ifpm_note=IFPM_NOTE)
    write_raster(score_path, score, ref_profile, ifpm_note=IFPM_NOTE)

    valid_fraction = float(np.sum(valid & inside)) / inside_total if inside_total else 0.0
    filled_cells = raw_valid_after - raw_valid_before

    manifest_rows = [
        {"field": "criterion_name", "value": CRITERION_NAME},
        {"field": "claim_level", "value": CLAIM_LEVEL},
        {"field": "source_metric", "value": SOURCE_METRIC},
        {"field": "source_unit", "value": SOURCE_UNIT},
        {"field": "native_resolution", "value": NATIVE_RESOLUTION},
        {"field": "target_grid", "value": TARGET_GRID},
        {"field": "resampling_method", "value": RESAMPLING_METHOD},
        {"field": "effective_resolution_warning", "value": EFFECTIVE_RESOLUTION_WARNING},
        {"field": "source_lineage", "value": LINEAGE},
        {"field": "source_raster", "value": str(CHIRPS_NATIVE)},
        {"field": "reference_raster", "value": str(REF)},
        {"field": "raw_output", "value": str(raw_path)},
        {"field": "score_output", "value": str(score_path)},
        {"field": "raw_min_mm_per_season", "value": round(raw_min, 3)},
        {"field": "raw_mean_mm_per_season", "value": round(raw_mean, 3)},
        {"field": "raw_max_mm_per_season", "value": round(raw_max, 3)},
        {"field": "normalization", "value": "max-normalize to [0,1]; highest-rainfall cell -> 1.0"},
        {"field": "nodata_policy", "value": (
            "Resampling-edge NoData slivers inside V1 are filled with "
            "nearest-valid-value extrapolation via a Euclidean distance "
            "transform (scipy.ndimage.distance_transform_edt). The holes are "
            "edge slivers (connected to the raster outside) left by the 0.05 deg "
            "source not tiling the UTM-35S V1 polygon boundary exactly; they are "
            "a coarse-to-fine geometry artifact, not real missing rainfall. "
            "Cells outside V1 stay NoData. Documented imputation per AGENTS.md "
            "NoData policy."
        )},
        {"field": "v1_inside_cells", "value": inside_total},
        {"field": "valid_fraction_before_edge_fill", "value": round(raw_frac_before, 6)},
        {"field": "valid_fraction_after_edge_fill", "value": round(raw_frac_after, 6)},
        {"field": "fill_hole_cells", "value": fill_stats["hole_cells"]},
        {"field": "fill_interior_holes", "value": fill_stats["interior_holes"]},
        {"field": "fill_edge_sliver_holes", "value": fill_stats["edge_sliver_holes"]},
        {"field": "edge_filled_cells", "value": int(filled_cells)},
        {"field": "valid_cell_count", "value": int(np.sum(valid & inside))},
        {"field": "valid_cell_fraction", "value": round(valid_fraction, 6)},
        {"field": "built", "value": str(date.today())},
    ]
    with (OUT_DIR / f"{CRITERION_NAME}_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["field", "value"])
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(f"resampled {SOURCE_METRIC}: {raw_min:.1f}-{raw_max:.1f} mm/season -> 0-1 score")
    print(f"holes inside V1: {fill_stats['hole_cells']} cells "
          f"({fill_stats['edge_sliver_holes']} edge slivers, {fill_stats['interior_holes']} interior)")
    print(f"edge-filled {int(filled_cells)} resampling-edge sliver cells inside V1")
    print(f"valid inside V1: {raw_frac_before:.4f} -> {raw_frac_after:.4f} after edge fill")
    print(f"wrote {BOUNDARY_ID} / {EXPERIMENT_ID} / criteria to {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
