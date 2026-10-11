#!/usr/bin/env python3
"""Create QA outputs for V1 SRTM DEM and slope preprocessing."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.ticker import FuncFormatter
from matplotlib.colors import LightSource
from rasterio.features import geometry_mask


ROOT = Path(__file__).resolve().parents[2]
DATASET_ID = "srtm_1arcsec_zimbabwe"
OUTPUT_ROOT_ID = "zimbabwe_terrain_hydrology_factors"  # outputs folder name (differs from the id since 2026-10-11 rename)
OUT_DIR = ROOT / f"outputs/{OUTPUT_ROOT_ID}/terrain_preprocessing"
V1_GPKG = ROOT / "outputs/zimbabwe_boundary/zimbabwe_boundary.gpkg"
DEM = OUT_DIR / "zimbabwe_dem_utm35s_30m.tif"
BUFFERED_DEM = OUT_DIR / "zimbabwe_dem_buffered_utm35s_30m.tif"
SLOPE = OUT_DIR / "zimbabwe_slope_degrees_utm35s_30m.tif"
DIAGNOSTICS_CSV = OUT_DIR / "zimbabwe_terrain_preprocessing_diagnostics.csv"
QA_PNG = OUT_DIR / "zimbabwe_terrain_qa_map.png"
QA_PDF = OUT_DIR / "zimbabwe_terrain_qa_map.pdf"
HANDOFF = OUT_DIR / "v1_terrain_preprocessing_handoff.md"
DST_CRS = "EPSG:32735"
NODATA = -9999.0
MIN_VALID_INSIDE = 0.98


def load_boundary() -> gpd.GeoDataFrame:
    return gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(DST_CRS)


def read_raster(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as src:
        data = src.read(1).astype("float32")
        profile = src.profile.copy()
        profile["bounds"] = src.bounds
        profile["res"] = src.res
    return data, profile


def valid_stats(path: Path, geometry) -> dict[str, object]:
    with rasterio.open(path) as src:
        data = src.read(1).astype("float32")
        inside = geometry_mask([geometry], out_shape=data.shape, transform=src.transform, invert=True)
        valid = inside & np.isfinite(data) & (data != src.nodata)
        values = data[valid]
        if values.size == 0:
            raise ValueError(f"No valid cells inside V1 for {path.name}")
        valid_fraction = float(valid.sum() / inside.sum())
        return {
            "raster": path.name,
            "crs": str(src.crs),
            "width": src.width,
            "height": src.height,
            "count": src.count,
            "dtype": src.dtypes[0],
            "nodata": src.nodata,
            "res_x": src.res[0],
            "res_y": src.res[1],
            "inside_cells": int(inside.sum()),
            "valid_inside_cells": int(valid.sum()),
            "valid_inside_fraction": round(valid_fraction, 6),
            "min": round(float(np.nanmin(values)), 6),
            "max": round(float(np.nanmax(values)), 6),
            "mean": round(float(np.nanmean(values)), 6),
            "p02": round(float(np.nanpercentile(values, 2)), 6),
            "p98": round(float(np.nanpercentile(values, 98)), 6),
        }


def write_diagnostics(rows: list[dict[str, object]]) -> None:
    with DIAGNOSTICS_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def assert_outputs(rows: list[dict[str, object]]) -> None:
    by_name = {row["raster"]: row for row in rows}
    dem = by_name[DEM.name]
    slope = by_name[SLOPE.name]
    for row in rows:
        if row["crs"] != DST_CRS or row["count"] != 1 or row["nodata"] != NODATA:
            raise ValueError(f"Unexpected raster profile: {row}")
        if float(row["valid_inside_fraction"]) < MIN_VALID_INSIDE:
            raise ValueError(f"Valid-cell fraction below threshold: {row}")
    if dem["width"] != slope["width"] or dem["height"] != slope["height"]:
        raise ValueError("DEM and slope dimensions differ")
    if slope["min"] < 0 or slope["max"] <= 0:
        raise ValueError("Slope raster has invalid range")


def raster_extent(bounds) -> list[float]:
    return [bounds.left, bounds.right, bounds.bottom, bounds.top]


def km_formatter(value, _pos) -> str:
    return f"{value / 1000:.0f}"


def plot_qa(boundary: gpd.GeoDataFrame) -> None:
    dem, dem_profile = read_raster(DEM)
    slope, slope_profile = read_raster(SLOPE)
    dem_show = np.where(dem == NODATA, np.nan, dem)
    slope_show = np.where(slope == NODATA, np.nan, slope)
    hillshade = LightSource(azdeg=315, altdeg=45).hillshade(np.nan_to_num(dem_show, nan=np.nanmean(dem_show)))

    fig, axes = plt.subplots(1, 2, figsize=(12, 6.2), constrained_layout=True)
    axes[0].imshow(hillshade, cmap="gray", extent=raster_extent(dem_profile["bounds"]), origin="upper")
    dem_img = axes[0].imshow(dem_show, cmap="terrain", extent=raster_extent(dem_profile["bounds"]), origin="upper", alpha=0.62)
    boundary.boundary.plot(ax=axes[0], color="black", linewidth=0.8)
    axes[0].set_title("Upper Mzingwane DEM with QA hillshade")
    fig.colorbar(dem_img, ax=axes[0], shrink=0.76, label="Elevation (m)")

    slope_img = axes[1].imshow(slope_show, cmap="magma", extent=raster_extent(slope_profile["bounds"]), origin="upper")
    boundary.boundary.plot(ax=axes[1], color="white", linewidth=0.8)
    axes[1].set_title("Upper Mzingwane slope diagnostic")
    fig.colorbar(slope_img, ax=axes[1], shrink=0.76, label="Slope (degrees)")

    for ax in axes:
        ax.set_xlabel("Easting (km, EPSG:32735)")
        ax.set_ylabel("Northing (km, EPSG:32735)")
        ax.xaxis.set_major_formatter(FuncFormatter(km_formatter))
        ax.yaxis.set_major_formatter(FuncFormatter(km_formatter))
        ax.set_aspect("equal", adjustable="box")
        ax.grid(alpha=0.12)

    fig.savefig(QA_PNG, dpi=220)
    fig.savefig(QA_PDF)
    plt.close(fig)


def write_handoff(rows: list[dict[str, object]]) -> None:
    dem = next(row for row in rows if row["raster"] == DEM.name)
    slope = next(row for row in rows if row["raster"] == SLOPE.name)
    HANDOFF.write_text(
        "\n".join(
            [
                "# SRTM V1 Terrain Preprocessing Handoff",
                "",
                f"Updated: {date.today().isoformat()}",
                "",
                "Status: DEM and slope diagnostics produced for controlled V1 terrain preprocessing.",
                "",
                f"- DEM: `{DEM.relative_to(ROOT)}`",
                f"- Buffered DEM: `{BUFFERED_DEM.relative_to(ROOT)}`",
                f"- Slope: `{SLOPE.relative_to(ROOT)}`",
                f"- Diagnostics: `{DIAGNOSTICS_CSV.relative_to(ROOT)}`",
                f"- QA map: `{QA_PNG.relative_to(ROOT)}`",
                "",
                f"- DEM valid inside V1: `{dem['valid_inside_fraction']}`",
                f"- DEM elevation range: `{dem['min']}` to `{dem['max']}` m",
                f"- Slope valid inside V1: `{slope['valid_inside_fraction']}`",
                f"- Slope range: `{slope['min']}` to `{slope['max']}` degrees",
                "",
                "Scope limits: no CHIRPS download, no flow accumulation, no drainage proxy, no AHP overlay, and no flood-risk interpretation were performed.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    boundary = load_boundary()
    rows = [valid_stats(DEM, boundary.geometry.iloc[0]), valid_stats(SLOPE, boundary.geometry.iloc[0])]
    assert_outputs(rows)
    write_diagnostics(rows)
    plot_qa(boundary)
    write_handoff(rows)
    print(f"wrote {DIAGNOSTICS_CSV.relative_to(ROOT)}")
    print(f"wrote {QA_PNG.relative_to(ROOT)}")
    print(f"wrote {QA_PDF.relative_to(ROOT)}")
    print(f"wrote {HANDOFF.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
