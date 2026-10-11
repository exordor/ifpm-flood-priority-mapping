#!/usr/bin/env python3
"""Plot V1 CHIRPS rainfall comparison panels and handoff notes."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import TwoSlopeNorm


ROOT = Path(__file__).resolve().parents[2]
DATASET_ID = "chirps_v3_zimbabwe"
OUTPUT_ROOT_ID = "zimbabwe_chirps_v3_rainfall"  # outputs folder name (differs from the id since 2026-10-11 rename)
OUT_DIR = ROOT / f"outputs/{OUTPUT_ROOT_ID}/rainfall_comparison"
SUMMARY_CSV = OUT_DIR / "zimbabwe_rainfall_metric_summary.csv"
BOARD_PNG = OUT_DIR / "zimbabwe_mentor_chirps_rainfall_comparison_board.png"
BOARD_PDF = OUT_DIR / "zimbabwe_mentor_chirps_rainfall_comparison_board.pdf"
CAPTION_MD = OUT_DIR / "zimbabwe_mentor_chirps_rainfall_caption.md"
CAPTION_TXT = OUT_DIR / "zimbabwe_mentor_chirps_rainfall_caption.txt"
HANDOFF_MD = OUT_DIR / "v1_chirps_rainfall_comparison_handoff.md"
V1_GPKG = ROOT / "outputs/zimbabwe_boundary/zimbabwe_boundary.gpkg"


def read_summary() -> list[dict[str, str]]:
    if not SUMMARY_CSV.exists():
        raise FileNotFoundError(f"Missing summary: {SUMMARY_CSV}. Run compare_zimbabwe_chirps_rainfall_metrics.py first.")
    with SUMMARY_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def v1_boundary() -> gpd.GeoDataFrame:
    return gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs("EPSG:4326")


def raster_data(path: Path) -> tuple[np.ndarray, list[float], float | None]:
    with rasterio.open(path) as src:
        data = src.read(1).astype("float32")
        data = np.where(data == src.nodata, np.nan, data)
        extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
        return data, extent, src.nodata


def panel_title(row: dict[str, str]) -> str:
    return row["metric_id"].replace("_", " ").replace("pct", "%")


def plot_one(ax, row: dict[str, str], boundary: gpd.GeoDataFrame, colorbar: bool = True) -> None:
    path = ROOT / row["native_grid_raster"]
    data, extent, _ = raster_data(path)
    is_anomaly = row["unit"] == "percent"
    vmin = float(np.nanmin(data))
    vmax = float(np.nanmax(data))
    cmap = "viridis"
    norm = None
    if is_anomaly and vmin < 0 < vmax:
        cmap = "RdBu"
        norm = TwoSlopeNorm(vcenter=0, vmin=vmin, vmax=vmax)
    elif is_anomaly:
        cmap = "YlOrRd" if vmin >= 0 else "Blues_r"
    image = ax.imshow(data, extent=extent, origin="upper", cmap=cmap, norm=norm)
    boundary.boundary.plot(ax=ax, color="black", linewidth=1.0)
    ax.set_title(panel_title(row), fontsize=10)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal", adjustable="box")
    if colorbar:
        plt.colorbar(image, ax=ax, fraction=0.046, pad=0.02, label=row["unit"])


def write_individual_panels(rows: list[dict[str, str]], boundary: gpd.GeoDataFrame) -> None:
    for row in rows:
        fig, ax = plt.subplots(figsize=(5.2, 5.2), constrained_layout=True)
        plot_one(ax, row, boundary)
        ax.text(0.02, 0.02, row["time_window"], transform=ax.transAxes, fontsize=8, va="bottom")
        png = OUT_DIR / f"panel_{row['metric_id']}.png"
        pdf = OUT_DIR / f"panel_{row['metric_id']}.pdf"
        fig.savefig(png, dpi=220)
        fig.savefig(pdf)
        plt.close(fig)


def write_board(rows: list[dict[str, str]], boundary: gpd.GeoDataFrame) -> None:
    fig, axes = plt.subplots(3, 3, figsize=(14, 13), constrained_layout=True)
    for ax, row in zip(axes.ravel(), rows, strict=True):
        plot_one(ax, row, boundary)
        ax.set_xlabel("")
        ax.set_ylabel("")
    fig.suptitle(
        "Upper Mzingwane Catchment: CHIRPS Rainfall Sensitivity Comparison (Native Grid)",
        fontsize=14,
    )
    fig.savefig(BOARD_PNG, dpi=220)
    fig.savefig(BOARD_PDF)
    plt.close(fig)


def markdown_table(rows: list[dict[str, str]]) -> list[str]:
    lines = ["| Metric | Window | Unit | V1 mean | Role |", "|---|---:|---:|---:|---|"]
    for row in rows:
        lines.append(
            f"| `{row['metric_id']}` | {row['time_window']} | {row['unit']} | {float(row['v1_mean']):.2f} | {row['interpretation']} |"
        )
    return lines


def write_text_outputs(rows: list[dict[str, str]]) -> None:
    caption = "\n".join(
        [
            "# Caption: V1 CHIRPS Rainfall Sensitivity Comparison",
            "",
            "Figure X. CHIRPS v3 rainfall sensitivity comparison for the V1 working catchment. "
            "The panels compare long-term annual rainfall, recent annual rainfall, recent annual anomaly, "
            "long-term and recent rainy-season totals, rainy-season anomaly, monthly peak rainfall, pentad "
            "peak rainfall, and a derived daily RNL peak for one recent rainy season.",
            "",
            "Source note: CHIRPS v3 final Africa annual, monthly, and pentad GeoTIFFs are used for the "
            "long-term, seasonal, and pentad indicators. The daily panel uses CHIRPS v3 daily RNL COGs "
            "clipped to the V1 bounding box.",
            "",
            "Boundary and scale note: The V1 boundary is a prototype-only working catchment accepted with "
            "waiver. CHIRPS remains at native coarse rainfall scale or V1 zonal summary scale; it is not "
            "resampled to the 30 m terrain grid and this figure is not a flood-risk map or AHP overlay.",
        ]
    )
    CAPTION_MD.write_text(caption + "\n", encoding="utf-8")
    CAPTION_TXT.write_text(caption.replace("# Caption: V1 CHIRPS Rainfall Sensitivity Comparison\n\n", "") + "\n", encoding="utf-8")

    handoff = "\n".join(
        [
            "# V1 CHIRPS Rainfall Comparison Handoff",
            "",
            f"Updated: {date.today().isoformat()}",
            "",
            "Status: rainfall sensitivity comparison produced for mentor review. No AHP weights, weighted overlay, flood-risk map, or intervention interpretation is included.",
            "",
            "Key point: the comparison does not pick one rainfall criterion. It shows how the rainfall signal changes when the timestep and temporal window change.",
            "",
            "Metric summary:",
            "",
            *markdown_table(rows),
            "",
            "Recommended mentor decision: choose whether the first prototype should use annual climate background, rainy-season accumulation, recent anomaly, or short-duration extreme rainfall as the rainfall criterion.",
            "",
            "Daily caveat: the daily RNL metric is derived by downscaling pentad/monthly CHIRPS using ERA5 daily ratios. It is useful for a sensitivity check, but should not be treated as more authoritative than the pentad/monthly product.",
            "",
            "Scale caveat: CHIRPS is about 0.05 degree, much coarser than SRTM terrain. Keep it native or summarize it to V1/sub-basin units until a modelling-unit decision is accepted.",
        ]
    )
    HANDOFF_MD.write_text(handoff + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_summary()
    boundary = v1_boundary()
    write_individual_panels(rows, boundary)
    write_board(rows, boundary)
    write_text_outputs(rows)
    print(f"wrote {BOARD_PNG.relative_to(ROOT)}")
    print(f"wrote {HANDOFF_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
