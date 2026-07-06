#!/usr/bin/env python3
"""Inventory downloaded SRTMGL1 tiles and draw a V1 coverage check map."""

from __future__ import annotations

import csv
import hashlib
import zipfile
from datetime import date
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import rasterio
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


ROOT = Path(__file__).resolve().parents[2]
INPUTS = [ROOT / "outputs/v1_working_boundary/srtm_v1_tile_plan.gpkg", ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"]
OUTPUTS = [ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/srtm_tile_inventory.csv"]
DATASET_ID = "srtm_1arcsec_zimbabwe_prototype"
RAW_DIR = ROOT / f"data/raw/{DATASET_ID}"
OUT_DIR = ROOT / f"outputs/{DATASET_ID}"
PLAN_GPKG = ROOT / "outputs/v1_working_boundary/srtm_v1_tile_plan.gpkg"
V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
MANIFEST_CSV = OUT_DIR / "srtm_raw_file_manifest.csv"
INVENTORY_CSV = OUT_DIR / "srtm_tile_inventory.csv"
COVERAGE_PNG = OUT_DIR / "srtm_tile_coverage_check.png"
HANDOFF_MD = OUT_DIR / "srtm_download_handoff.md"
EXPECTED_TILES = ["S22E028", "S22E029", "S21E028", "S21E029", "S20E028", "S20E029"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def archive_for_tile(tile: str) -> Path:
    matches = sorted(RAW_DIR.glob(f"{tile}*.zip"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one ZIP archive for {tile}, found {len(matches)}")
    return matches[0]


def hgt_member(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".hgt")]
    if len(members) != 1:
        raise ValueError(f"Expected one .hgt member in {path.name}, found {members}")
    return members[0]


def raster_uri(path: Path, member: str) -> str:
    return f"zip://{path.resolve()}!{member}"


def inventory_tile(tile: str) -> dict[str, str | int | float | None]:
    path = archive_for_tile(tile)
    member = hgt_member(path)
    with rasterio.open(raster_uri(path, member)) as src:
        bounds = src.bounds
        row = {
            "tile_name": tile,
            "archive_path": str(path.relative_to(ROOT)),
            "hgt_member": member,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "driver": src.driver,
            "crs": str(src.crs) if src.crs else "",
            "width": src.width,
            "height": src.height,
            "count": src.count,
            "dtype": src.dtypes[0],
            "nodata": src.nodata,
            "res_x": src.res[0],
            "res_y": src.res[1],
            "bounds_left": bounds.left,
            "bounds_bottom": bounds.bottom,
            "bounds_right": bounds.right,
            "bounds_top": bounds.top,
            "transform": str(src.transform),
        }
    return row


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def plot_coverage(rows: list[dict[str, object]]) -> None:
    tiles = gpd.read_file(PLAN_GPKG, layer="srtm_tiles").to_crs("EPSG:4326")
    bbox = gpd.read_file(PLAN_GPKG, layer="v1_bbox_5km_buffer").to_crs("EPSG:4326")
    v1 = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs("EPSG:4326")
    downloaded = pd.DataFrame(rows)[["tile_name", "archive_path"]]
    tiles = tiles.merge(downloaded, on="tile_name", how="left")

    fig, ax = plt.subplots(figsize=(8, 8), constrained_layout=True)
    tiles.plot(ax=ax, color="#f7fbff", edgecolor="#6baed6", linewidth=1.2)
    tiles.dropna(subset=["archive_path"]).plot(ax=ax, color="#c6dbef", edgecolor="#2171b5", alpha=0.45)
    bbox.boundary.plot(ax=ax, color="#636363", linewidth=1.2, linestyle="--")
    v1.plot(ax=ax, color="#fee8c8", edgecolor="#e34a33", alpha=0.55, linewidth=1.5)

    for _, row in tiles.iterrows():
        centroid = row.geometry.centroid
        ax.text(centroid.x, centroid.y, row["tile_name"], ha="center", va="center", fontsize=8)

    ax.set_title("SRTM Tile Coverage Check for the Upper Mzingwane Prototype Catchment", fontsize=12, weight="bold")
    ax.set_xlabel("Longitude (EPSG:4326)")
    ax.set_ylabel("Latitude (EPSG:4326)")
    ax.grid(True, alpha=0.2)
    ax.set_aspect("equal", adjustable="box")
    ax.legend(
        handles=[
            Patch(facecolor="#c6dbef", edgecolor="#2171b5", alpha=0.45, label="Downloaded SRTM tile"),
            Patch(facecolor="#fee8c8", edgecolor="#e34a33", alpha=0.55, label="Prototype catchment"),
            Line2D([0], [0], color="#636363", linestyle="--", label="5 km buffered catchment extent"),
        ],
        loc="lower left",
        fontsize=8,
        frameon=True,
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(COVERAGE_PNG, dpi=220)
    plt.close(fig)


def write_handoff(rows: list[dict[str, object]]) -> None:
    total_bytes = sum(int(row["bytes"]) for row in rows)
    HANDOFF_MD.write_text(
        "\n".join(
            [
                "# SRTM V1 Download And Inventory Handoff",
                "",
                f"Updated: {date.today().isoformat()}",
                "",
                "Status: downloaded and inventoried for controlled V1 terrain diagnostics only.",
                "",
                f"- Dataset id: `{DATASET_ID}`",
                f"- Tile count: `{len(rows)}`",
                f"- Tiles: `{', '.join(row['tile_name'] for row in rows)}`",
                f"- Total source archive bytes: `{total_bytes}`",
                f"- Raw manifest: `{MANIFEST_CSV.relative_to(ROOT)}`",
                f"- Raster inventory: `{INVENTORY_CSV.relative_to(ROOT)}`",
                f"- Coverage check: `{COVERAGE_PNG.relative_to(ROOT)}`",
                "",
                "Scope limits: no CHIRPS download, no slope or flow-accumulation derivation, no AHP overlay, and no flood-risk interpretation were performed.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    rows = [inventory_tile(tile) for tile in EXPECTED_TILES]
    write_csv(INVENTORY_CSV, rows)
    if not MANIFEST_CSV.exists():
        write_csv(MANIFEST_CSV, rows)
    plot_coverage(rows)
    write_handoff(rows)
    print(f"wrote {INVENTORY_CSV.relative_to(ROOT)}")
    print(f"wrote {COVERAGE_PNG.relative_to(ROOT)}")
    print(f"wrote {HANDOFF_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
