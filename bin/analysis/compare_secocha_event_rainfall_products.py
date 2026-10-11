#!/usr/bin/env python3
"""Compare CHIRPS v3 ``sat`` and ``rnl`` event-window products.

The two products are alternative daily temporal allocations of the same CHIRPS
family, not independent gauge observations.  This diagnostic keeps that
distinction explicit and makes the choice between them auditable.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import rasterio


ROOT = Path(__file__).resolve().parents[2]
SAT_MANIFEST = ROOT / "outputs/secocha_2023_validation/rainfall/event_rainfall_manifest.json"
RNL_MANIFEST = ROOT / "outputs/secocha_2023_validation/rainfall_rnl/event_rainfall_rnl_manifest.json"
OUT_DIR = ROOT / "outputs/secocha_2023_validation/rainfall"
OUT_JSON = OUT_DIR / "rainfall_sat_vs_rnl_comparison.json"
OUT_CSV = OUT_DIR / "rainfall_sat_vs_rnl_comparison.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_local_file(entry: dict[str, object]) -> tuple[Path, dict[str, object]]:
    path = ROOT / str(entry["path"])
    if not path.exists():
        raise FileNotFoundError(path)
    recorded = str(entry.get("sha256", ""))
    actual = sha256(path)
    if not recorded or recorded != actual:
        raise RuntimeError(f"local rainfall artifact hash mismatch: {path}")
    return path, {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": actual}


def validate_manifest(manifest_path: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = {
        "boundary_id": "secocha_reference_extent",
        "event_id": "secocha_2023_historical_hazard_event",
        "event_date": "2023-02-05",
        "claim_level": "validation_candidate",
    }
    for key, expected in required.items():
        if manifest.get(key) != expected:
            raise RuntimeError(f"{manifest_path} has unexpected {key}: {manifest.get(key)!r}")
    if manifest.get("enters_pim_score") is not False:
        raise RuntimeError(f"{manifest_path} event rainfall must remain outside the PIM score")
    if manifest.get("boundary_sha256") != "4b6d0fe0775c706860190c5b9248deeeec539399831be1577007487151907d4b":
        raise RuntimeError(f"{manifest_path} boundary hash does not match active Secocha boundary")
    if manifest.get("date_range") != {"start": "2023-01-07", "end": "2023-02-10", "days": 35}:
        raise RuntimeError(f"{manifest_path} date range is not the frozen event window")
    local = manifest.get("local_files")
    if not isinstance(local, list) or len(local) < 2:
        raise RuntimeError(f"{manifest_path} must list stack and accumulation artifacts")
    records = []
    for entry in local:
        if not isinstance(entry, dict):
            raise RuntimeError(f"{manifest_path} has malformed local_files entry")
        _, record = resolve_local_file(entry)
        records.append(record)
    return manifest, records


def raster_profile(dataset: rasterio.io.DatasetReader) -> dict[str, object]:
    return {
        "shape": [dataset.count, dataset.height, dataset.width],
        "crs": str(dataset.crs),
        "transform": [dataset.transform.a, dataset.transform.b, dataset.transform.c, dataset.transform.d, dataset.transform.e, dataset.transform.f],
        "resolution": list(dataset.res),
        "nodata": dataset.nodata,
    }


def expected_dates() -> list[str]:
    start = date.fromisoformat("2023-01-07")
    return [(start + timedelta(days=index)).isoformat() for index in range(35)]


def read_raster(path: Path, expected_count: int) -> tuple[np.ndarray, list[str], dict[str, object]]:
    with rasterio.open(path) as dataset:
        if dataset.count != expected_count:
            raise RuntimeError(f"{path} expected {expected_count} bands, found {dataset.count}")
        array = dataset.read().astype("float32")
        descriptions = [description for description in dataset.descriptions]
        if any(description is None for description in descriptions):
            raise RuntimeError(f"{path} has unnamed bands")
        return array, [str(item) for item in descriptions], raster_profile(dataset)


def read_stack(manifest_path: Path) -> tuple[dict[str, object], np.ndarray, list[str]]:
    manifest, local_records = validate_manifest(manifest_path)
    stack_path = ROOT / manifest["local_files"][0]["path"]
    array, dates, profile = read_raster(stack_path, expected_count=35)
    if dates != expected_dates():
        raise RuntimeError(f"{stack_path} band dates do not match the declared 35-day window")
    declared_transform = manifest.get("stack_transform")
    if declared_transform is not None:
        declared = list(declared_transform)
        # The acquisition manifest stores the affine's (a, e, c, f) terms;
        # the raster profile keeps all six GDAL affine terms.
        if len(declared) == 4:
            expected_transform = [profile["transform"][0], profile["transform"][4], profile["transform"][2], profile["transform"][5]]
        else:
            expected_transform = profile["transform"]
        if declared != expected_transform:
            raise RuntimeError(f"{stack_path} transform differs from its manifest")
    if manifest.get("stack_shape") != profile["shape"]:
        raise RuntimeError(f"{stack_path} shape differs from its manifest")
    return {"manifest": manifest, "stack_path": stack_path, "profile": profile, "local_records": local_records}, array, dates


def stats(values: np.ndarray) -> dict[str, float | int | None]:
    finite = values[np.isfinite(values) & (values != -9999.0)]
    return {
        "mean_mm": float(finite.mean()) if finite.size else None,
        "max_mm": float(finite.max()) if finite.size else None,
        "valid_pixels": int(finite.size),
    }


def main() -> None:
    sat_meta, sat, sat_dates = read_stack(SAT_MANIFEST)
    rnl_meta, rnl, rnl_dates = read_stack(RNL_MANIFEST)
    if sat_dates != rnl_dates or sat.shape != rnl.shape:
        raise RuntimeError("sat/rnl stacks do not share the same dates and grid")
    if sat_meta["profile"] != rnl_meta["profile"]:
        raise RuntimeError("sat/rnl stacks do not share the same native grid profile")
    for key in ("boundary_id", "boundary_sha256", "event_id", "event_date", "query_bounds_wgs84", "date_range"):
        if sat_meta["manifest"].get(key) != rnl_meta["manifest"].get(key):
            raise RuntimeError(f"sat/rnl manifests disagree on {key}")

    daily_rows = []
    for index, current in enumerate(sat_dates):
        s = sat[index]
        r = rnl[index]
        common = np.isfinite(s) & np.isfinite(r) & (s != -9999.0) & (r != -9999.0)
        difference = s[common] - r[common]
        daily_rows.append(
            {
                "date": current,
                "sat": stats(s),
                "rnl": stats(r),
                "difference_sat_minus_rnl_mean_mm": float(difference.mean()) if difference.size else None,
                "absolute_difference_mean_mm": float(np.abs(difference).mean()) if difference.size else None,
                "common_pixels": int(common.sum()),
            }
        )

    sat_accum_manifest = sat_meta["manifest"]
    rnl_accum_manifest = rnl_meta["manifest"]
    sat_accum_path = ROOT / sat_accum_manifest["local_files"][1]["path"]
    rnl_accum_path = ROOT / rnl_accum_manifest["local_files"][1]["path"]
    sat_accum, labels, sat_accum_profile = read_raster(sat_accum_path, expected_count=5)
    rnl_accum, rnl_labels, rnl_accum_profile = read_raster(rnl_accum_path, expected_count=5)
    expected_accum_labels = [
        "cum_1d_2023-02-05",
        "cum_3d_2023-02-03_2023-02-05",
        "cum_7d_2023-01-30_2023-02-05",
        "cum_30d_2023-01-07_2023-02-05",
        "post_5d_2023-02-06_2023-02-10",
    ]
    if labels != expected_accum_labels or rnl_labels != expected_accum_labels:
        raise RuntimeError("rainfall accumulation band labels do not match the event windows")
    if sat_accum_profile != rnl_accum_profile or sat_accum_profile != sat_meta["profile"] | {"shape": [5, sat_meta["profile"]["shape"][1], sat_meta["profile"]["shape"][2]]}:
        raise RuntimeError("sat/rnl accumulation rasters do not share the stack grid")
    accumulation_rows = []
    for index, label in enumerate(labels):
        s = sat_accum[index]
        r = rnl_accum[index]
        common = np.isfinite(s) & np.isfinite(r) & (s != -9999.0) & (r != -9999.0)
        difference = s[common] - r[common]
        ratio_mask = common & (np.abs(r) > 1e-6)
        ratios = s[ratio_mask] / r[ratio_mask]
        accumulation_rows.append(
            {
                "window": label,
                "sat": stats(s),
                "rnl": stats(r),
                "difference_sat_minus_rnl_mean_mm": float(difference.mean()) if difference.size else None,
                "absolute_difference_mean_mm": float(np.abs(difference).mean()) if difference.size else None,
                "median_sat_to_rnl_ratio": float(np.median(ratios)) if ratios.size else None,
                "common_pixels": int(common.sum()),
            }
        )

    result = {
        "dataset_id": "secocha_2023_event_rainfall_chirps_v3_sat_vs_rnl",
        "event_id": "secocha_2023_historical_hazard_event",
        "event_date": "2023-02-05",
        "boundary_id": sat_meta["manifest"]["boundary_id"],
        "boundary_sha256": sat_meta["manifest"]["boundary_sha256"],
        "query_bounds_wgs84": sat_meta["manifest"]["query_bounds_wgs84"],
        "date_range": sat_meta["manifest"]["date_range"],
        "claim_level": "validation_candidate",
        "enters_pim_score": False,
        "interpretation": "sat and rnl are alternative CHIRPS v3 daily temporal allocations/sensitivity products, not independent observed rainfall datasets or gauge validation.",
        "native_grid": sat_meta["profile"],
        "sat_manifest": {"path": str(SAT_MANIFEST.relative_to(ROOT)), "sha256": sha256(SAT_MANIFEST)},
        "rnl_manifest": {"path": str(RNL_MANIFEST.relative_to(ROOT)), "sha256": sha256(RNL_MANIFEST)},
        "local_lineage": {
            "sat": {
                "stack": sat_meta["local_records"][0],
                "accumulation": sat_meta["local_records"][1],
            },
            "rnl": {
                "stack": rnl_meta["local_records"][0],
                "accumulation": rnl_meta["local_records"][1],
            },
            "stack_profiles": {"sat": sat_meta["profile"], "rnl": rnl_meta["profile"]},
            "accumulation_profiles": {"sat": sat_accum_profile, "rnl": rnl_accum_profile},
            "stack_dates": sat_dates,
            "accumulation_labels": labels,
        },
        "daily_rows": daily_rows,
        "accumulation_rows": accumulation_rows,
        "next_step": "Use gauge or authenticated sub-daily product if the 14:00-14:17 trigger intensity must be tested; do not select sat/rnl after inspecting only one result.",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["window,sat_mean_mm,rnl_mean_mm,sat_minus_rnl_mean_mm,absolute_difference_mean_mm,median_sat_to_rnl_ratio,common_pixels"]
    # The nested stats are easier to read in JSON; the CSV is a compact handoff table.
    for index, row in enumerate(accumulation_rows):
        values = [
            row["window"],
            row["sat"]["mean_mm"],
            row["rnl"]["mean_mm"],
            row["difference_sat_minus_rnl_mean_mm"],
            row["absolute_difference_mean_mm"],
            row["median_sat_to_rnl_ratio"],
            row["common_pixels"],
        ]
        lines.append(",".join(str(value) for value in values))
    OUT_CSV.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"json": str(OUT_JSON.relative_to(ROOT)), "csv": str(OUT_CSV.relative_to(ROOT)), "accumulation_rows": accumulation_rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
