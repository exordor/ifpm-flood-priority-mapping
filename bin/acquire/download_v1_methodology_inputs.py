#!/usr/bin/env python3
"""Download public inputs for the V1 full methodology evidence sweep."""

from __future__ import annotations

import csv
import hashlib
import shutil
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/v1_full_methodology_evidence_sweep"
MANIFEST = OUT_DIR / "source_manifest.csv"
USER_AGENT = "IFPM-Methodology-V1/1.0 (research prototype; contact via project owner)"

SOURCES = [
    {
        "dataset_id": "esa_worldcover_2021_v1_methodology",
        "role": "land_use_environment_rehabilitation",
        "url": "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_S21E027_Map.tif",
        "local_path": "data/raw/esa_worldcover_2021_v1_methodology/ESA_WorldCover_10m_2021_v200_S21E027_Map.tif",
    },
    {
        "dataset_id": "worldpop_zwe_2020_v1_methodology",
        "role": "socioeconomic_population_exposure",
        "url": "https://data.worldpop.org/GIS/Population/Global_2000_2020/2020/ZWE/zwe_ppp_2020_UNadj.tif",
        "local_path": "data/raw/worldpop_zwe_2020_v1_methodology/zwe_ppp_2020_UNadj.tif",
    },
    {
        "dataset_id": "ghsl_zimbabwe_v1_methodology",
        "role": "built_up_surface_exposure_crosscheck",
        "url": "https://data.humdata.org/dataset/9befff21-f81d-43f1-9fcb-15b09a5f9103/resource/ca0feb6a-149d-4dd0-afb1-a681bf37a8ee/download/ghs_built_s_e2025_r2023a_54009_100_v1_0_zwe.tif",
        "local_path": "data/raw/ghsl_zimbabwe_v1_methodology/ghs_built_s_e2025_r2023a_54009_100_v1_0_zwe.tif",
    },
    {
        "dataset_id": "ghsl_zimbabwe_v1_methodology",
        "role": "population_exposure_crosscheck",
        "url": "https://data.humdata.org/dataset/9befff21-f81d-43f1-9fcb-15b09a5f9103/resource/a712437c-f0ce-46ea-a4c8-ec01a8041ee4/download/ghs_pop_e2025_r2023a_54009_100_v1_0_zwe.tif",
        "local_path": "data/raw/ghsl_zimbabwe_v1_methodology/ghs_pop_e2025_r2023a_54009_100_v1_0_zwe.tif",
    },
    {
        "dataset_id": "jrc_global_surface_water_v1_methodology",
        "role": "surface_water_occurrence",
        "url": "https://storage.googleapis.com/global-surface-water/downloads/occurrence/occurrence_20E_20S.tif",
        "local_path": "data/raw/jrc_global_surface_water_v1_methodology/occurrence_20E_20S.tif",
    },
    {
        "dataset_id": "jrc_global_surface_water_v1_methodology",
        "role": "surface_water_seasonality",
        "url": "https://storage.googleapis.com/global-surface-water/downloads/seasonality/seasonality_20E_20S.tif",
        "local_path": "data/raw/jrc_global_surface_water_v1_methodology/seasonality_20E_20S.tif",
    },
    {
        "dataset_id": "jrc_global_surface_water_v1_methodology",
        "role": "surface_water_recurrence",
        "url": "https://storage.googleapis.com/global-surface-water/downloads/recurrence/recurrence_20E_20S.tif",
        "local_path": "data/raw/jrc_global_surface_water_v1_methodology/recurrence_20E_20S.tif",
    },
    {
        "dataset_id": "jrc_global_surface_water_v1_methodology",
        "role": "surface_water_change",
        "url": "https://storage.googleapis.com/global-surface-water/downloads/change/change_20E_20S.tif",
        "local_path": "data/raw/jrc_global_surface_water_v1_methodology/change_20E_20S.tif",
    },
    {
        "dataset_id": "jrc_global_surface_water_v1_methodology",
        "role": "surface_water_transitions",
        "url": "https://storage.googleapis.com/global-surface-water/downloads/transitions/transitions_20E_20S.tif",
        "local_path": "data/raw/jrc_global_surface_water_v1_methodology/transitions_20E_20S.tif",
    },
    {
        "dataset_id": "dfo_global_flood_archive_v1_methodology",
        "role": "historical_global_flood_archive",
        "url": "https://data.humdata.org/dataset/1fd855de-57c6-42b3-83e1-9cf989b0f70d/resource/984cc240-b2b7-4266-9f61-5715a9e10ff5/download/wlf_nhr_fl_dfomasterlist_20190418.zip",
        "local_path": "data/raw/dfo_global_flood_archive_v1_methodology/wlf_nhr_fl_dfomasterlist_20190418.zip",
    },
    {
        "dataset_id": "wdpca_zimbabwe_v1_methodology",
        "role": "official_protected_conserved_areas",
        "url": "https://data.humdata.org/dataset/ef375df9-81d3-4cd9-9461-2aa6cda6ae45/resource/a15eef56-23bf-4969-a07c-6d98911c2825/download/protected_conserved_areas_wdpca.gpkg",
        "local_path": "data/raw/wdpca_zimbabwe_v1_methodology/protected_conserved_areas_wdpca.gpkg",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_prior_manifest() -> dict[str, str]:
    """Map previously recorded local_path -> sha256 so a truncated/corrupted
    existing file is detected and re-fetched instead of being reused forever."""
    if not MANIFEST.exists():
        return {}
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
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


def download(source: dict[str, str], recorded_sha: str = "") -> dict[str, str]:
    path = ROOT / source["local_path"]
    status = "reused_existing"
    if path.exists() and path.stat().st_size > 0:
        if recorded_sha and sha256(path) != recorded_sha:
            print(
                f"existing {path.name} sha mismatch with prior manifest; re-downloading",
                file=sys.stderr,
            )
            status = "downloaded"
    if not path.exists() or path.stat().st_size == 0 or status == "downloaded":
        status = "downloaded"
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".part")
        if tmp.exists():
            tmp.unlink()
        req = urllib.request.Request(source["url"], headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=180) as response, tmp.open("wb") as handle:
                declared = response.headers.get("Content-Length")
                expected = int(declared) if declared and declared.isdigit() else None
                shutil.copyfileobj(response, handle, length=1024 * 1024)
                if expected is not None:
                    _verify_size(tmp, expected, source["url"])
        except Exception:
            if tmp.exists():
                tmp.unlink()
            raise
        tmp.replace(path)
    return {
        **source,
        "local_path": str(path.relative_to(ROOT)),
        "status": status,
        "bytes": str(path.stat().st_size),
        "sha256": sha256(path),
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def write_manifest(rows: list[dict[str, str]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = ["dataset_id", "role", "url", "local_path", "status", "bytes", "sha256", "checked_at_utc"]
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    prior = load_prior_manifest()
    rows = [download(source, prior.get(source["local_path"], "")) for source in SOURCES]
    write_manifest(rows)
    total = sum(int(row["bytes"]) for row in rows)
    print(f"wrote {MANIFEST.relative_to(ROOT)}")
    print(f"files: {len(rows)}; bytes: {total}")


if __name__ == "__main__":
    main()
