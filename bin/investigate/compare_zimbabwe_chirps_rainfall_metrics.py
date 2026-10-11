#!/usr/bin/env python3
"""Compute V1 native-grid CHIRPS rainfall comparison metrics."""

from __future__ import annotations

import csv
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask


ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import write_raster as _write_raster
from functools import partial
write_raster = partial(_write_raster, sanitize=True)
DATASET_ID = "chirps_v3_zimbabwe"
OUTPUT_ROOT_ID = "zimbabwe_chirps_v3_rainfall"  # outputs folder name (differs from the id since 2026-10-11 rename)
OUT_DIR = ROOT / f"outputs/{OUTPUT_ROOT_ID}/rainfall_comparison"
MANIFEST_CSV = OUT_DIR / "zimbabwe_chirps_raw_file_manifest.csv"
SUMMARY_CSV = OUT_DIR / "zimbabwe_rainfall_metric_summary.csv"
CORR_CSV = OUT_DIR / "zimbabwe_rainfall_metric_correlation.csv"
RASTER_DIR = OUT_DIR / "rasters"
V1_GPKG = ROOT / "outputs/zimbabwe_boundary/zimbabwe_boundary.gpkg"
NODATA = -9999.0
RECENT_YEARS = set(range(2020, 2025))
RAINY_SEASONS = range(1981, 2024)
RECENT_SEASONS = range(2019, 2024)


def rainy_months(season_start: int) -> list[tuple[int, int]]:
    return [(season_start, 11), (season_start, 12), (season_start + 1, 1), (season_start + 1, 2), (season_start + 1, 3)]


def read_manifest() -> list[dict[str, str]]:
    if not MANIFEST_CSV.exists():
        raise FileNotFoundError(f"Missing manifest: {MANIFEST_CSV}. Run download_zimbabwe_chirps_rainfall_inputs.py first.")
    with MANIFEST_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def v1_geometry() -> list[dict]:
    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs("EPSG:4326")
    if len(boundary) != 1 or boundary.geometry.iloc[0].is_empty:
        raise ValueError("Expected one non-empty V1 working boundary")
    return [boundary.geometry.iloc[0].__geo_interface__]


def local_path(row: dict[str, str]) -> Path:
    return ROOT / row["local_path"]


def load_masked(path: Path, geometry: list[dict]) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as src:
        data, transform = mask(src, geometry, crop=True, filled=True, nodata=NODATA)
        array = data[0].astype("float32")
        array[array == NODATA] = np.nan
        profile = src.profile.copy()
        profile.update(transform=transform, height=array.shape[0], width=array.shape[1], count=1, dtype="float32", nodata=NODATA)
        return array, profile


def stack(records: list[dict[str, str]], geometry: list[dict]) -> tuple[np.ndarray, dict]:
    arrays: list[np.ndarray] = []
    profile: dict | None = None
    for row in records:
        array, current_profile = load_masked(local_path(row), geometry)
        arrays.append(array)
        profile = current_profile if profile is None else profile
    if not arrays or profile is None:
        raise ValueError("No rasters selected for metric")
    return np.stack(arrays), profile


def season_sum(records: list[dict[str, str]], season_start: int, geometry: list[dict]) -> tuple[np.ndarray, dict]:
    wanted = {(str(y), str(m)) for y, m in rainy_months(season_start)}
    selected = [row for row in records if (row["year"], row["month"]) in wanted]
    if len(selected) != 5:
        raise ValueError(f"Season {season_start}-{season_start + 1} has {len(selected)} monthly files, expected 5")
    data, profile = stack(selected, geometry)
    valid = np.isfinite(data)
    summed = np.where(valid.any(axis=0), np.nansum(data, axis=0), np.nan).astype("float32")
    return summed, profile
def nanmean_axis0(data: np.ndarray) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        return np.nanmean(data, axis=0)


def nanmax_axis0(data: np.ndarray) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        return np.nanmax(data, axis=0)


def stats(metric_id: str, array: np.ndarray, metadata: dict[str, str], path: Path) -> dict[str, str]:
    values = array[np.isfinite(array)]
    if values.size == 0:
        raise ValueError(f"No valid cells for {metric_id}")
    return {
        "metric_id": metric_id,
        **metadata,
        "valid_cell_count": str(values.size),
        "v1_min": f"{float(np.nanmin(values)):.6f}",
        "v1_mean": f"{float(np.nanmean(values)):.6f}",
        "v1_max": f"{float(np.nanmax(values)):.6f}",
        "native_grid_raster": str(path.relative_to(ROOT)),
        "overlay_status": "native_or_zonal_summary_only_not_30m_overlay",
    }


def metric_rows(manifest: list[dict[str, str]], geometry: list[dict]) -> tuple[list[dict[str, str]], dict[str, Path]]:
    annual = [r for r in manifest if r["input_role"] == "annual_africa_tif"]
    monthly = [r for r in manifest if r["input_role"] == "monthly_africa_tif"]
    pentad = [r for r in manifest if r["input_role"] == "pentad_africa_tif"]
    daily = [r for r in manifest if r["input_role"] == "daily_rnl_cog_v1_bbox"]

    rows: list[dict[str, str]] = []
    outputs: dict[str, Path] = {}

    annual_stack, annual_profile = stack(annual, geometry)
    annual_mean = nanmean_axis0(annual_stack)
    recent_annual = nanmean_axis0(np.stack([annual_stack[i] for i, r in enumerate(annual) if int(r["year"]) in RECENT_YEARS]))
    annual_anomaly_pct = np.where(annual_mean != 0, (recent_annual - annual_mean) / annual_mean * 100.0, np.nan)

    season_arrays = [season_sum(monthly, season, geometry)[0] for season in RAINY_SEASONS]
    _, monthly_profile = season_sum(monthly, 1981, geometry)
    rainy_mean = nanmean_axis0(np.stack(season_arrays))
    recent_rainy = nanmean_axis0(np.stack([season_sum(monthly, season, geometry)[0] for season in RECENT_SEASONS]))
    rainy_anomaly_pct = np.where(rainy_mean != 0, (recent_rainy - rainy_mean) / rainy_mean * 100.0, np.nan)

    recent_monthly_records = [r for r in monthly if any((r["year"], r["month"]) == (str(y), str(m)) for s in RECENT_SEASONS for y, m in rainy_months(s))]
    monthly_peak_stack, monthly_peak_profile = stack(recent_monthly_records, geometry)
    pentad_peak_stack, pentad_profile = stack(pentad, geometry)
    daily_peak_stack, daily_profile = stack(daily, geometry)
    monthly_peak = nanmax_axis0(monthly_peak_stack)
    pentad_peak = nanmax_axis0(pentad_peak_stack)
    daily_peak = nanmax_axis0(daily_peak_stack)

    specs = [
        ("annual_mean_1981_2024", annual_mean, annual_profile, "annual", "1981-2024", "mm/year", "long-term annual rainfall baseline"),
        ("annual_recent_mean_2020_2024", recent_annual, annual_profile, "annual", "2020-2024", "mm/year", "recent annual rainfall baseline"),
        ("annual_recent_anomaly_pct", annual_anomaly_pct, annual_profile, "annual", "2020-2024 vs 1981-2024", "percent", "recent annual anomaly"),
        ("rainy_season_mean_1981_2024", rainy_mean, monthly_profile, "monthly", "Nov-Mar seasons 1981/82-2023/24", "mm/season", "long-term rainy-season accumulated rainfall"),
        ("rainy_season_recent_mean_2019_2024", recent_rainy, monthly_profile, "monthly", "Nov-Mar seasons 2019/20-2023/24", "mm/season", "recent rainy-season accumulated rainfall"),
        ("rainy_season_recent_anomaly_pct", rainy_anomaly_pct, monthly_profile, "monthly", "2019/20-2023/24 vs 1981/82-2023/24", "percent", "recent rainy-season anomaly"),
        ("rainy_season_monthly_peak_2019_2024", monthly_peak, monthly_peak_profile, "monthly", "Nov-Mar seasons 2019/20-2023/24", "mm/month", "largest monthly rainfall in recent rainy seasons"),
        ("rainy_season_pentad_peak_2019_2024", pentad_peak, pentad_profile, "pentad", "Nov-Mar seasons 2019/20-2023/24", "mm/pentad", "largest pentad rainfall in recent rainy seasons"),
        ("daily_rnl_peak_2023_2024", daily_peak, daily_profile, "daily_rnl", "2023-11-01 to 2024-03-31", "mm/day", "derived daily RNL maximum for one recent rainy season"),
    ]
    for metric_id, array, profile, timestep, window, unit, interpretation in specs:
        out_path = RASTER_DIR / f"{metric_id}.tif"
        write_raster(out_path, array.astype("float32"), profile)
        outputs[metric_id] = out_path
        # daily_rnl is the only CHIRPS Real-time/Near-real-time (preliminary) product here;
        # annual/monthly/pentad Africa TIFs are final products. Do not treat the RNL peak as
        # commensurate with the final-product peaks in cross-metric interpretation.
        is_provisional = timestep == "daily_rnl"
        rows.append(stats(metric_id, array, {
            "product_timestep": timestep,
            "time_window": window,
            "unit": unit,
            "interpretation": interpretation,
            "product_provisional": "yes" if is_provisional else "no",
            "product_provisional_note": "CHIRPS RNL is preliminary real-time/near-real-time data" if is_provisional else "CHIRPS final product (Africa TIF)",
        }, out_path))
    return rows, outputs


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def correlations(outputs: dict[str, Path]) -> list[dict[str, str]]:
    arrays: dict[str, np.ndarray] = {}
    for metric_id, path in outputs.items():
        with rasterio.open(path) as src:
            data = src.read(1).astype("float32")
            arrays[metric_id] = np.where(data == src.nodata, np.nan, data).ravel()
    # daily_rnl is preliminary (RNL) data; flag any correlation pair that includes it so the
    # reader does not treat a provisional-vs-final correlation as methodologically commensurate.
    provisional = {"daily_rnl_peak_2023_2024"}
    rows: list[dict[str, str]] = []
    for left, a in arrays.items():
        for right, b in arrays.items():
            valid = np.isfinite(a) & np.isfinite(b)
            if int(valid.sum()) < 3 or float(np.nanstd(a[valid])) == 0.0 or float(np.nanstd(b[valid])) == 0.0:
                corr = ""
            else:
                corr = f"{float(np.corrcoef(a[valid], b[valid])[0, 1]):.6f}"
            pair_note = "includes_provisional_RNL_metric" if (left in provisional or right in provisional) else ""
            rows.append({"metric_a": left, "metric_b": right, "common_cell_count": str(int(valid.sum())), "pearson_r": corr, "provisional_pair_note": pair_note})
    return rows


def main() -> None:
    geometry = v1_geometry()
    summary_rows, outputs = metric_rows(read_manifest(), geometry)
    write_csv(SUMMARY_CSV, summary_rows)
    write_csv(CORR_CSV, correlations(outputs))
    print(f"wrote {SUMMARY_CSV.relative_to(ROOT)}")
    print(f"wrote {CORR_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
