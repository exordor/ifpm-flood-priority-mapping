#!/usr/bin/env python3
"""Download selected quantitative Sentinel assets through CDSE S3.

The catalog is the selection authority.  This acquisition stage only downloads
assets already listed there and records size/hash lineage.  Credentials are
read from an ignored local JSON file and never copied into outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

import boto3


ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "outputs/secocha_2023_validation/satellite_before_after/sentinel_catalog_manifest.json"
CREDENTIALS = ROOT / "data/tmp/cdse_s3_credentials.json"
OUT_DIR = ROOT / "outputs/secocha_2023_validation/satellite_before_after"
OUT_MANIFEST = OUT_DIR / "sentinel_pixel_download_manifest.json"
DATA_DIR = ROOT / "data/validation/secocha_2023_validation/satellite_before_after/pixels"

S2_ASSETS = {
    "B02_10m",
    "B03_10m",
    "B04_10m",
    "B08_10m",
    "SCL_20m",
    "safe_manifest",
    "product_metadata",
}
S1_ASSETS = {
    "vv",
    "vh",
    "safe_manifest",
    "schema-product-vv",
    "schema-product-vh",
    "schema-calibration-vv",
    "schema-calibration-vh",
    "schema-noise-vv",
    "schema-noise-vh",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def client_from_credentials() -> tuple[object, dict[str, object]]:
    if not CREDENTIALS.exists():
        raise FileNotFoundError(f"CDSE credentials are missing: {CREDENTIALS}")
    credentials = json.loads(CREDENTIALS.read_text(encoding="utf-8"))
    required = {"endpoint", "access_key", "secret_key", "region", "bucket"}
    if not required.issubset(credentials):
        raise RuntimeError("CDSE credential file is missing required fields")
    client = boto3.client(
        "s3",
        endpoint_url=credentials["endpoint"],
        aws_access_key_id=credentials["access_key"],
        aws_secret_access_key=credentials["secret_key"],
        region_name=credentials["region"],
    )
    return client, credentials


def normalize_key(href: str) -> str:
    if href.startswith("s3://eodata/"):
        return href.removeprefix("s3://eodata/")
    if href.startswith("https://") and "/eodata/" in href:
        return href.split("/eodata/", 1)[1]
    raise RuntimeError(f"unsupported eodata asset href: {href}")


def requested_assets(scene: dict[str, object]) -> list[str]:
    assets = scene.get("assets", {})
    if scene.get("collection") == "sentinel-1-grd":
        return [name for name in S1_ASSETS if name in assets]
    return [name for name in S2_ASSETS if name in assets]


def download_asset(client: object, bucket: str, key: str, target: Path, expected_size: int | None) -> dict[str, object]:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        actual_size = target.stat().st_size
        if expected_size is None or actual_size == expected_size:
            return {
                "path": str(target.relative_to(ROOT)),
                "bytes": actual_size,
                "sha256": sha256(target),
                "downloaded": False,
                "size_matches_catalog": True,
            }
    client.download_file(Bucket=bucket, Key=key, Filename=str(target))
    actual_size = target.stat().st_size
    size_matches = expected_size is None or actual_size == expected_size
    if not size_matches:
        target.unlink(missing_ok=True)
        raise RuntimeError(f"download size mismatch for {key}: expected {expected_size}, got {actual_size}")
    return {
        "path": str(target.relative_to(ROOT)),
        "bytes": actual_size,
        "sha256": sha256(target),
        "downloaded": True,
        "size_matches_catalog": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", choices=("core_s2", "s1_pair", "all"), default="core_s2")
    parser.add_argument("--manifest", default="auto")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    client, credentials = client_from_credentials()
    bucket = str(credentials["bucket"])
    roles = {
        "core_s2": {"s2_pre_event", "s2_post_3d"},
        "s1_pair": {"s1_pre", "s1_post"},
        "all": {scene["role"] for scene in catalog["selected_scenes"]},
    }[args.batch]
    selected = [scene for scene in catalog["selected_scenes"] if scene["role"] in roles]
    if len(selected) != len(roles):
        raise RuntimeError("catalog no longer contains all selected roles for the requested batch")

    run_started = datetime.now(timezone.utc)
    records: list[dict[str, object]] = []
    for scene in selected:
        for asset_name in requested_assets(scene):
            asset = scene["assets"][asset_name]
            key = normalize_key(asset["href"])
            target = DATA_DIR / scene["role"] / key.removeprefix("Sentinel-")
            record = download_asset(
                client,
                bucket,
                key,
                target,
                asset.get("file:size"),
            )
            records.append(
                {
                    "role": scene["role"],
                    "scene_id": scene["id"],
                    "collection": scene["collection"],
                    "asset": asset_name,
                    "s3_key": key,
                    **record,
                }
            )

    credential_hash = sha256(CREDENTIALS)
    manifest = {
        "dataset_id": "secocha_2023_sentinel_before_after_pixels",
        "event_id": catalog["event_id"],
        "event_date": catalog["event_date"],
        "boundary_id": catalog["boundary_id"],
        "boundary_sha256": catalog["boundary_sha256"],
        "catalog_manifest": str(CATALOG.relative_to(ROOT)),
        "catalog_manifest_sha256": sha256(CATALOG),
        "claim_level": "validation_candidate",
        "enters_pim_score": False,
        "batch": args.batch,
        "access_date": date.today().isoformat(),
        "run_started_utc": run_started.isoformat(),
        "run_finished_utc": datetime.now(timezone.utc).isoformat(),
        "credential_registry": {
            "path": str(CREDENTIALS.relative_to(ROOT)),
            "sha256": credential_hash,
            "secret_material_recorded": False,
            "credential_source": credentials.get("credential_source"),
        },
        "downloaded_assets": records,
        "asset_count": len(records),
        "downloaded_bytes": sum(record["bytes"] for record in records),
        "size_checks_passed": all(record["size_matches_catalog"] for record in records),
        "processing_note": "Raw calibrated/orthoready L1 or L2 assets downloaded only; quantitative S1/S2 comparison still requires processing, cloud masking, co-registration and analyst validation.",
    }
    manifest_path = OUT_MANIFEST if args.manifest == "auto" else ROOT / args.manifest
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "manifest": str(manifest_path.relative_to(ROOT)),
                "asset_count": manifest["asset_count"],
                "downloaded_bytes": manifest["downloaded_bytes"],
                "size_checks_passed": manifest["size_checks_passed"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
