#!/usr/bin/env python3
"""Download scoped CHIRPS inputs for the V1 rainfall comparison."""

from __future__ import annotations

import csv
import hashlib
import shutil
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import rasterio
from rasterio.windows import from_bounds


ROOT = Path(__file__).resolve().parents[1]
DATASET_ID = "chirps_v3_zimbabwe_prototype"
PLAN_SCRIPT = ROOT / "bin/plan_chirps_v1_rainfall_metrics.py"
OUT_DIR = ROOT / f"outputs/{DATASET_ID}/rainfall_comparison"
PLAN_CSV = OUT_DIR / "chirps_v1_download_plan.csv"
MANIFEST_CSV = OUT_DIR / "chirps_v1_raw_file_manifest.csv"
V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
BBOX_PAD_DEG = 0.1


def ensure_plan() -> None:
    if not PLAN_CSV.exists():
        import subprocess

        subprocess.run([sys.executable, str(PLAN_SCRIPT)], cwd=ROOT, check=True)


def read_plan() -> list[dict[str, str]]:
    ensure_plan()
    with PLAN_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def resolve(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


def v1_bbox() -> tuple[float, float, float, float]:
    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs("EPSG:4326")
    left, bottom, right, top = boundary.total_bounds
    return left - BBOX_PAD_DEG, bottom - BBOX_PAD_DEG, right + BBOX_PAD_DEG, top + BBOX_PAD_DEG


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_file(url: str, path: Path) -> str:
    if path.exists() and path.stat().st_size > 0:
        return "reused_existing"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    if tmp.exists():
        tmp.unlink()
    try:
        with urllib.request.urlopen(url, timeout=90) as response, tmp.open("wb") as handle:
            shutil.copyfileobj(response, handle, length=1024 * 1024)
        tmp.replace(path)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise
    return "downloaded"


def clip_daily_cog(url: str, path: Path, bbox: tuple[float, float, float, float]) -> str:
    if path.exists() and path.stat().st_size > 0:
        return "reused_existing"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    if tmp.exists():
        tmp.unlink()

    try:
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".cog"):
            with rasterio.open(url) as src:
                window = from_bounds(*bbox, transform=src.transform).round_offsets().round_lengths()
                data = src.read(1, window=window)
                transform = src.window_transform(window)
                profile = src.profile.copy()
                profile.update(
                    driver="GTiff",
                    height=data.shape[0],
                    width=data.shape[1],
                    transform=transform,
                    count=1,
                    compress="deflate",
                    tiled=True,
                    blockxsize=256,
                    blockysize=256,
                )
                with rasterio.open(tmp, "w", **profile) as dst:
                    dst.write(data, 1)
        tmp.replace(path)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise
    return "clipped_from_remote_cog"


def write_manifest(rows: list[dict[str, str]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with MANIFEST_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def process_row(item: dict[str, str], bbox: tuple[float, float, float, float]) -> dict[str, str]:
    local_path = resolve(item["local_path"])
    if item["download_mode"] == "remote_cog_v1_bbox_clip":
        status = clip_daily_cog(item["source_url"], local_path, bbox)
    else:
        status = download_file(item["source_url"], local_path)
    return {
        **item,
        "local_path": str(local_path.relative_to(ROOT)),
        "status": status,
        "bytes": str(local_path.stat().st_size),
        "sha256": sha256(local_path),
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    planned = read_plan()
    bbox = v1_bbox()
    manifest = [process_row(item, bbox) for item in planned]
    write_manifest(manifest)
    print(f"wrote {MANIFEST_CSV.relative_to(ROOT)}")
    print(f"available files: {len(manifest)}")


if __name__ == "__main__":
    main()
