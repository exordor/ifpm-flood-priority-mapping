#!/usr/bin/env python3
"""Standardize V1 hydrology evidence candidates to 0-1 for mentor review (no overlay).

Local TOOLING script. The terrain candidates (IFPM-055) already produced three 0-1 standardized
diagnostics, but the hydrology evidence - TWI (topographic wetness) and distance-to-drainage - has
no standardized candidate yet. This fills that gap with two 0-1 candidates using the SAME method
as the terrain standardization (2-98 percentile clip + min-max), so the hydrology candidates are
directly comparable to the terrain ones for mentor review.

Both candidates are flood-susceptibility / exposure diagnostics. They are CANDIDATE EVIDENCE for
mentor review, NOT overlay-ready criteria: per AGENTS.md and the V1 terrain reference grid rule, no
criterion enters AHP overlay, scoring, or interpretation until the mentor confirms the criteria
hierarchy (IFPM-D01/D04) and modelling unit (IFPM-D01).

Candidates:
  zimbabwe_twi_high_wetness_0_1.tif
      higher TWI -> higher diagnostic value (more accumulated wetness, more flood-susceptible).
      TWI = ln(As / tan(slope)); high values mark flat, wet, converging areas.
  zimbabwe_drainage_proximity_0_1.tif
      smaller distance-to-drainage -> higher diagnostic value (closer to streams = more flood
      exposure). Inverted: 0 at the stream, 1 far from it becomes 0.

Method (identical to standardize_zimbabwe_terrain.py): clip to the 2nd-98th percentile, min-max scale to
0-1, invert where lower raw values should mean higher diagnostic value (distance-to-drainage).
Grid-aligned to the V1 reference DEM via check_zimbabwe_raster_grid.py; NoData preserved as -9999.0.

Usage (from workspace root):
    .venv/bin/python bin/package/standardize_zimbabwe_hydrology.py
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import geometry_mask

try:
    import geopandas as gpd
except ImportError as exc:
    raise SystemExit(f"missing dependency: {exc}") from exc

ROOT = Path(__file__).resolve().parents[2]
INPUTS = [ROOT / "outputs/zimbabwe_terrain_hydrology_factors/hydrology_derivatives/zimbabwe_twi.tif", ROOT / "outputs/zimbabwe_terrain_hydrology_factors/hydrology_derivatives/zimbabwe_distance_to_drainage_t500.tif", ROOT / "outputs/zimbabwe_boundary/zimbabwe_boundary.gpkg"]
OUTPUTS = [ROOT / "outputs/zimbabwe_terrain_hydrology_factors/hydrology_standardization/zimbabwe_twi_high_wetness_0_1.tif", ROOT / "outputs/zimbabwe_terrain_hydrology_factors/hydrology_standardization/zimbabwe_drainage_proximity_0_1.tif"]
import sys
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import write_raster
from _lib.standardization import percentile_minmax
TWI = ROOT / "outputs/zimbabwe_terrain_hydrology_factors/hydrology_derivatives/zimbabwe_twi.tif"
DIST = ROOT / "outputs/zimbabwe_terrain_hydrology_factors/hydrology_derivatives/zimbabwe_distance_to_drainage_t500.tif"
V1_GPKG = ROOT / "outputs/zimbabwe_boundary/zimbabwe_boundary.gpkg"
V1_LAYER = "v1_working_boundary"

OUT_DIR = ROOT / "outputs/zimbabwe_terrain_hydrology_factors/hydrology_standardization"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CLIP_LOW = 2.0
CLIP_HIGH = 98.0
NODATA = -9999.0


def main() -> None:
    boundary = gpd.read_file(V1_GPKG, layer=V1_LAYER)
    rows = []

    candidates = [
        ("zimbabwe_twi_high_wetness_0_1.tif", TWI, "twi_high_wetness",
         "higher TWI -> higher diagnostic value (wet/converging flood-susceptible areas)", False),
        ("zimbabwe_drainage_proximity_0_1.tif", DIST, "drainage_proximity",
         "closer to drainage -> higher diagnostic value (flood exposure)", True),
    ]

    for outname, src_path, indicator, direction, invert in candidates:
        with rasterio.open(src_path) as ds:
            data = ds.read(1).astype("float64")
            nodata = ds.nodata if ds.nodata is not None else NODATA
            profile = ds.profile
            bnd = boundary.to_crs(ds.crs)
            geom = [g for g in bnd.geometry if g is not None and not g.is_empty][0]
            inside = geometry_mask([geom], out_shape=data.shape, transform=ds.transform, invert=True)

        out, low, high = percentile_minmax(
            data,
            inside,
            nodata=nodata,
            invert=invert,
            p_low=CLIP_LOW,
            p_high=CLIP_HIGH,
            output_nodata=nodata,
        )
        valid = inside & np.isfinite(data) & (data != nodata)
        mean_out = float(np.nanmean(out[valid]))
        n_valid = int(valid.sum())
        out_path = OUT_DIR / outname
        write_raster(out_path, out, profile)

        # raw input stats (inside V1)
        raw_valid = inside & np.isfinite(data) & (data != nodata)
        raw_vals = data[raw_valid]
        rows.append({
            "output": str(out_path.relative_to(ROOT)),
            "source": str(src_path.relative_to(ROOT)),
            "indicator": indicator,
            "method": "percentile_clip_minmax_2_98",
            "direction": direction,
            "invert": invert,
            "clip_low": round(low, 4),
            "clip_high": round(high, 4),
            "input_min": round(float(np.nanmin(raw_vals)), 4),
            "input_max": round(float(np.nanmax(raw_vals)), 4),
            "input_mean": round(float(np.nanmean(raw_vals)), 4),
            "output_min": 0.0,
            "output_max": 1.0,
            "output_mean": round(mean_out, 6),
            "valid_cells": int(n_valid),
            "valid_cell_fraction": round(n_valid / data.size, 4),
            "eligible_for_overlay": "no_pending_criteria_decision",
            "notes": "hydrology candidate evidence for mentor review; not flood risk; no overlay until criteria hierarchy confirmed",
        })
        print(f"  {indicator}: clip [{low:.3f}, {high:.3f}], mean={mean_out:.4f}, valid={n_valid}")

    # diagnostics CSV
    diag_csv = OUT_DIR / "zimbabwe_hydrology_standardization_diagnostics.csv"
    with open(diag_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {diag_csv}")

    # processing note
    note = f"""# V1 hydrology evidence standardization (candidate, no overlay)

Generated: {datetime.now(timezone.utc).isoformat(timespec="seconds")} (UTC) by `bin/package/standardize_zimbabwe_hydrology.py`.

## Purpose

Fill the gap left by IFPM-055: terrain had three 0-1 candidates, but hydrology had none. This
produces two hydrology candidate diagnostics using the SAME method as the terrain standardization
(2-98 percentile clip + min-max), so terrain and hydrology candidates are comparable for mentor
review.

## Candidates

| candidate | source | direction |
|---|---|---|
| `zimbabwe_twi_high_wetness_0_1.tif` | TWI (ln(As/tan(slope))) | higher TWI -> higher diagnostic value |
| `zimbabwe_drainage_proximity_0_1.tif` | distance-to-drainage (t500) | closer -> higher diagnostic value (inverted) |

## Method

For each: clip to the 2nd-98th percentile of valid V1 cells, min-max scale to 0-1, invert where
lower raw values mean higher diagnostic value. NoData preserved as -9999.0.

## Status

CANDIDATE EVIDENCE for mentor review. NOT overlay-ready and NOT a flood-risk criterion. Per
AGENTS.md and the V1 terrain reference grid rule, no criterion enters AHP overlay, scoring, or
interpretation until the mentor confirms the criteria hierarchy (IFPM-D01/D04) and modelling unit
(IFPM-D01). Run `bin/package/check_zimbabwe_raster_grid.py` before any future overlay use.
"""
    (OUT_DIR / "v1_hydrology_standardization_handoff.md").write_text(note, encoding="utf-8")
    print(f"wrote {OUT_DIR / 'v1_hydrology_standardization_handoff.md'}")


if __name__ == "__main__":
    main()
