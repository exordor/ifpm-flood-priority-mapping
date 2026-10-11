#!/usr/bin/env python3
"""Prepare V1 raster evidence layers for the full methodology sweep."""

from __future__ import annotations

import csv
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/v1_full_methodology_evidence_sweep"
RASTER_DIR = OUT_DIR / "rasters"
SUMMARY_CSV = OUT_DIR / "v1_raster_layer_summary.csv"
LANDCOVER_CSV = OUT_DIR / "v1_worldcover_class_area.csv"
GSW_CSV = OUT_DIR / "v1_jrc_surface_water_summary.csv"
GHSL_CSV = OUT_DIR / "v1_ghsl_summary.csv"

V1_GPKG = ROOT / "outputs/zimbabwe_boundary/zimbabwe_boundary.gpkg"
WORLDCOVER = ROOT / "data/raw/esa_worldcover_2021_zimbabwe/ESA_WorldCover_10m_2021_v200_S21E027_Map.tif"
WORLDPOP = ROOT / "data/raw/worldpop_2020_zimbabwe/zwe_ppp_2020_UNadj.tif"
GHSL_BUILT = ROOT / "data/raw/ghsl_zimbabwe/ghs_built_s_e2025_r2023a_54009_100_v1_0_zwe.tif"
GHSL_POP = ROOT / "data/raw/ghsl_zimbabwe/ghs_pop_e2025_r2023a_54009_100_v1_0_zwe.tif"
GSW_DIR = ROOT / "data/raw/jrc_global_surface_water_zimbabwe"

WORLD_COVER_CLASSES = {
    10: "Tree cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare/sparse vegetation",
    80: "Permanent water",
    90: "Herbaceous wetland",
}


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def v1_geometry(crs) -> list[dict]:
    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(crs)
    if len(boundary) != 1 or boundary.geometry.iloc[0].is_empty:
        raise ValueError("Expected one non-empty V1 boundary")
    return [boundary.geometry.iloc[0].__geo_interface__]


def clip_raster(src_path: Path, out_name: str, fill_value: float | int | None = None) -> tuple[Path, np.ndarray, dict]:
    out_path = RASTER_DIR / out_name
    with rasterio.open(src_path) as src:
        nodata = src.nodata if fill_value is None else fill_value
        data, transform = mask(src, v1_geometry(src.crs), crop=True, filled=True, nodata=nodata)
        profile = src.profile.copy()
        profile.update(driver="GTiff", height=data.shape[1], width=data.shape[2], transform=transform, nodata=nodata, compress="deflate")
        with rasterio.open(out_path, "w", **profile) as dst:
            dst.write(data)
    return out_path, data[0], profile


def raster_summary(label: str, path: Path, data: np.ndarray, nodata: float | int | None) -> dict[str, object]:
    valid = np.ones(data.shape, dtype=bool)
    if nodata is not None:
        valid &= data != nodata
    if data.dtype.kind == "f":
        valid &= np.isfinite(data)
    values = data[valid].astype("float64")
    return {
        "layer": label,
        "artifact": rel(path),
        "valid_cells": int(values.size),
        "min": float(values.min()) if values.size else np.nan,
        "mean": float(values.mean()) if values.size else np.nan,
        "max": float(values.max()) if values.size else np.nan,
        "sum": float(values.sum()) if values.size else np.nan,
    }


def worldcover_rows(data: np.ndarray) -> list[dict[str, object]]:
    total = int((data != 0).sum())
    rows = []
    for value, count in zip(*np.unique(data[data != 0], return_counts=True), strict=False):
        rows.append(
            {
                "class_value": int(value),
                "class_name": WORLD_COVER_CLASSES.get(int(value), "Unknown"),
                "cell_count": int(count),
                "area_km2_approx": float(count) * 0.0001,
                "share_of_valid_pct": float(count) / total * 100 if total else 0.0,
            }
        )
    return rows


def gsw_note(label: str) -> str:
    if label in {"occurrence", "recurrence"}:
        return "0-100 percent water-history layer; nonzero cells indicate mapped water history"
    if label == "seasonality":
        return "0-12 months/year water seasonality layer; nonzero cells indicate seasonal water"
    return "categorical layer; summarize counts, do not interpret mean as a continuous metric"


def ghsl_rows(summaries: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in summaries:
        if str(row["layer"]).startswith("ghsl_"):
            rows.append(
                {
                    "layer": row["layer"],
                    "artifact": row["artifact"],
                    "valid_cells": row["valid_cells"],
                    "min": row["min"],
                    "mean": row["mean"],
                    "max": row["max"],
                    "sum": row["sum"],
                    "interpretation_note": "GHSL is an exposure cross-check; do not treat as socioeconomic vulnerability by itself",
                }
            )
    return rows


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RASTER_DIR.mkdir(parents=True, exist_ok=True)
    summaries = []

    wc_path, wc, _ = clip_raster(WORLDCOVER, "v1_worldcover_2021_native_10m.tif", 0)
    summaries.append(raster_summary("worldcover_2021", wc_path, wc, 0))
    write_csv(LANDCOVER_CSV, worldcover_rows(wc))

    wp_path, wp, wp_profile = clip_raster(WORLDPOP, "v1_worldpop_2020_unadj_native.tif")
    summaries.append(raster_summary("worldpop_2020_unadj", wp_path, wp, wp_profile["nodata"]))

    ghsl_built_path, ghsl_built, ghsl_built_profile = clip_raster(GHSL_BUILT, "v1_ghsl_built_surface_2025_native.tif")
    summaries.append(raster_summary("ghsl_built_surface_2025", ghsl_built_path, ghsl_built, ghsl_built_profile["nodata"]))
    ghsl_pop_path, ghsl_pop, ghsl_pop_profile = clip_raster(GHSL_POP, "v1_ghsl_population_2025_native.tif")
    summaries.append(raster_summary("ghsl_population_2025", ghsl_pop_path, ghsl_pop, ghsl_pop_profile["nodata"]))
    write_csv(GHSL_CSV, ghsl_rows(summaries))

    gsw_rows = []
    for src_path in sorted(GSW_DIR.glob("*.tif")):
        label = src_path.stem.replace("_20E_20S", "")
        out_path, data, _ = clip_raster(src_path, f"v1_jrc_gsw_{label}.tif", 255)
        summaries.append(raster_summary(f"jrc_gsw_{label}", out_path, data, 255))
        valid = data != 255
        values = data[valid].astype("float64")
        gsw_rows.append(
            {
                "layer": label,
                "artifact": rel(out_path),
                "valid_cells": int(values.size),
                "nonzero_cells": int((values > 0).sum()),
                "mean": float(values.mean()) if values.size else np.nan,
                "max": float(values.max()) if values.size else np.nan,
                "interpretation_note": gsw_note(label),
            }
        )
    write_csv(GSW_CSV, gsw_rows)
    write_csv(SUMMARY_CSV, summaries)
    print(f"wrote {SUMMARY_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
