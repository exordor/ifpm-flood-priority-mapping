#!/usr/bin/env python3
"""Download or stage the planned SRTMGL1 tiles for the V1 prototype."""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
INPUTS = [ROOT / "outputs/v1_working_boundary/srtm_v1_tile_plan.csv"]
OUTPUTS = [ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/srtm_raw_file_manifest.csv"]
PLAN_CSV = ROOT / "outputs/v1_working_boundary/srtm_v1_tile_plan.csv"
RAW_DIR = ROOT / "data/raw/srtm_1arcsec_zimbabwe_prototype"
TMP_DIR = ROOT / "data/tmp/srtm_1arcsec_zimbabwe_prototype"
OUT_DIR = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype"
MANIFEST_CSV = OUT_DIR / "srtm_raw_file_manifest.csv"
DEFAULT_SOURCE_BASE = "https://step.esa.int/auxdata/dem/SRTMGL1/"
USER_AGENT = "IFPM-SRTM-V1/1.0 (research prototype; contact via project owner)"


class LoginRequired(RuntimeError):
    """Raised when the source appears to require browser login or authorization."""


def load_tiles() -> list[str]:
    if not PLAN_CSV.exists():
        raise FileNotFoundError(f"Missing tile plan: {PLAN_CSV.relative_to(ROOT)}")
    with PLAN_CSV.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    tiles = [row["tile_name"] for row in rows]
    expected = {"S22E028", "S22E029", "S21E028", "S21E029", "S20E028", "S20E029"}
    if set(tiles) != expected:
        raise ValueError(f"Unexpected SRTM tile set: {tiles}")
    return tiles


def tile_filename(tile: str) -> str:
    return f"{tile}.SRTMGL1.hgt.zip"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_zip(path: Path, tile: str) -> str:
    if not zipfile.is_zipfile(path):
        raise ValueError(f"Downloaded file is not a ZIP archive: {path.name}")
    with zipfile.ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".hgt")]
    if not members:
        raise ValueError(f"ZIP archive has no .hgt member: {path.name}")
    if not any(tile in Path(name).name for name in members):
        raise ValueError(f"ZIP archive does not look like tile {tile}: {members}")
    return members[0]


def request(url: str, method: str = "GET") -> Request:
    return Request(url, method=method, headers={"User-Agent": USER_AGENT})


def inspect_url(url: str) -> dict[str, str]:
    try:
        with urlopen(request(url, "HEAD"), timeout=30) as response:
            status = getattr(response, "status", 200)
            headers = response.headers
    except HTTPError as exc:
        if exc.code in {401, 403}:
            raise LoginRequired(f"source returned HTTP {exc.code}: {url}") from exc
        raise
    except URLError as exc:
        raise RuntimeError(f"cannot reach source URL: {url}") from exc

    content_type = headers.get("Content-Type", "")
    if status in {401, 403} or "text/html" in content_type.lower():
        raise LoginRequired(f"source returned login-like response: {status} {content_type} {url}")
    return {
        "http_status": str(status),
        "content_type": content_type,
        "content_length": headers.get("Content-Length", ""),
        "last_modified": headers.get("Last-Modified", ""),
        "etag": headers.get("ETag", ""),
    }


def download_tile(tile: str, source_base: str) -> dict[str, str]:
    filename = tile_filename(tile)
    url = source_base.rstrip("/") + "/" + filename
    target = RAW_DIR / filename
    metadata = inspect_url(url)

    if target.exists():
        member = validate_zip(target, tile)
        status = "already_present"
    else:
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        partial = TMP_DIR / f"{filename}.part"
        try:
            with urlopen(request(url), timeout=120) as response, partial.open("wb") as handle:
                content_type = response.headers.get("Content-Type", "")
                if "text/html" in content_type.lower():
                    raise LoginRequired(f"download returned HTML/login-like content: {url}")
                shutil.copyfileobj(response, handle)
        except HTTPError as exc:
            if exc.code in {401, 403}:
                raise LoginRequired(f"download requires login or authorization: {url}") from exc
            raise
        member = validate_zip(partial, tile)
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        partial.replace(target)
        status = "downloaded"

    return {
        "tile_name": tile,
        "status": status,
        "source_url": url,
        "raw_path": str(target.relative_to(ROOT)),
        "hgt_member": member,
        "bytes": str(target.stat().st_size),
        "sha256": sha256(target),
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **metadata,
    }


def stage_manual_tile(tile: str, source_dir: Path) -> dict[str, str]:
    filename = tile_filename(tile)
    candidates = [
        source_dir / filename,
        source_dir / f"{tile}.hgt.zip",
        source_dir / f"{tile}.zip",
    ]
    source = next((path for path in candidates if path.exists()), None)
    if source is None:
        raise FileNotFoundError(f"Manual source folder has no file for {tile}")
    member = validate_zip(source, tile)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    target = RAW_DIR / filename
    if source.resolve() != target.resolve():
        shutil.copy2(source, target)
    return {
        "tile_name": tile,
        "status": "staged_from_manual_download",
        "source_url": f"manual_source/{source.name}",
        "raw_path": str(target.relative_to(ROOT)),
        "hgt_member": member,
        "bytes": str(target.stat().st_size),
        "sha256": sha256(target),
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "http_status": "manual",
        "content_type": "application/zip",
        "content_length": str(target.stat().st_size),
        "last_modified": "",
        "etag": "",
    }


def write_manifest(rows: list[dict[str, str]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with MANIFEST_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-base", default=DEFAULT_SOURCE_BASE)
    parser.add_argument("--manual-source-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tiles = load_tiles()
    rows: list[dict[str, str]] = []
    try:
        for tile in tiles:
            if args.manual_source_dir:
                rows.append(stage_manual_tile(tile, args.manual_source_dir))
            else:
                rows.append(download_tile(tile, args.source_base))
    except LoginRequired as exc:
        print(f"LOGIN_REQUIRED: {exc}", file=sys.stderr)
        print("Stop here. Let the user handle login/authorization or provide manual downloads.", file=sys.stderr)
        return 2
    if rows:
        write_manifest(rows)
        print(f"wrote {MANIFEST_CSV.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
