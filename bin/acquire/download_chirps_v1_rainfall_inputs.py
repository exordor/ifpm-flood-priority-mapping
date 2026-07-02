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


ROOT = Path(__file__).resolve().parents[2]
INPUTS = [ROOT / "outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/chirps_v1_download_plan.csv"]
OUTPUTS = [ROOT / "outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/chirps_v1_raw_file_manifest.csv"]
DATASET_ID = "chirps_v3_zimbabwe_prototype"
PLAN_SCRIPT = ROOT / "bin/acquire/plan_chirps_v1_rainfall_metrics.py"
OUT_DIR = ROOT / f"outputs/{DATASET_ID}/rainfall_comparison"
PLAN_CSV = OUT_DIR / "chirps_v1_download_plan.csv"
MANIFEST_CSV = OUT_DIR / "chirps_v1_raw_file_manifest.csv"
V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
BBOX_PAD_DEG = 0.1
USER_AGENT = "IFPM-CHIRPS-V1/1.0 (research prototype; contact via project owner)"


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


def load_prior_manifest() -> dict[str, str]:
    """Map previously recorded local_path -> sha256 so a truncated/corrupted
    existing file is detected and re-fetched instead of being reused forever."""
    if not MANIFEST_CSV.exists():
        return {}
    with MANIFEST_CSV.open(newline="", encoding="utf-8") as handle:
        return {
            row["local_path"]: row.get("sha256", "")
            for row in csv.DictReader(handle)
            if row.get("local_path")
        }


def _verify_size(tmp: Path, expected: int | None, url: str) -> None:
    """Raise if the streamed file does not match the server-declared Content-Length.
    Servers using chunked transfer (no Content-Length) skip this check."""
    if expected is None:
        return
    actual = tmp.stat().st_size
    if actual != expected:
        raise IOError(
            f"download truncated: got {actual} bytes, expected {expected} from {url}"
        )


def _validate_tif(path: Path) -> None:
    """Probe that a written GeoTIFF is openable and non-empty (catches partial writes)."""
    with rasterio.open(path) as chk:
        if chk.width < 1 or chk.height < 1 or chk.count < 1:
            raise IOError(f"written raster is empty: {path.name}")


def download_file(url: str, path: Path, recorded_sha: str = "") -> str:
    if path.exists() and path.stat().st_size > 0:
        if recorded_sha and sha256(path) != recorded_sha:
            print(
                f"existing {path.name} sha mismatch with prior manifest; re-downloading",
                file=sys.stderr,
            )
        else:
            return "reused_existing"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    if tmp.exists():
        tmp.unlink()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            declared = response.headers.get("Content-Length")
            expected = int(declared) if declared and declared.isdigit() else None
            with tmp.open("wb") as handle:
                shutil.copyfileobj(response, handle, length=1024 * 1024)
        _verify_size(tmp, expected, url)
        tmp.replace(path)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise
    return "downloaded"


def clip_daily_cog(
    url: str, path: Path, bbox: tuple[float, float, float, float], recorded_sha: str = ""
) -> str:
    if path.exists() and path.stat().st_size > 0:
        if recorded_sha and sha256(path) != recorded_sha:
            print(
                f"existing {path.name} sha mismatch with prior manifest; re-clipping",
                file=sys.stderr,
            )
        else:
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
        _validate_tif(tmp)
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


def process_row(
    item: dict[str, str], bbox: tuple[float, float, float, float], prior: dict[str, str]
) -> dict[str, str]:
    local_path = resolve(item["local_path"])
    recorded_sha = prior.get(str(local_path.relative_to(ROOT)), "")
    if item["download_mode"] == "remote_cog_v1_bbox_clip":
        status = clip_daily_cog(item["source_url"], local_path, bbox, recorded_sha)
    else:
        status = download_file(item["source_url"], local_path, recorded_sha)
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
    prior = load_prior_manifest()
    manifest = [process_row(item, bbox, prior) for item in planned]
    write_manifest(manifest)
    print(f"wrote {MANIFEST_CSV.relative_to(ROOT)}")
    print(f"available files: {len(manifest)}")


if __name__ == "__main__":
    main()
