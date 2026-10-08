#!/usr/bin/env python3
"""Pull an event-window CHIRPS daily rainfall subset for Secocha 2023.

The current Secocha PIM uses a seasonal CHIRPS climatology.  This script keeps
the 2023-02-05 event rainfall separate: it reads the native 0.05 degree daily
CHIRPS files through HTTP range requests, crops them to a buffered active
reference window, and writes a small native-grid stack plus event accumulations.
The result is validation context only and never changes PIM weights or scores.
"""

from __future__ import annotations

import hashlib
import json
import ssl
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter, MaxNLocator
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from shapely.geometry import mapping


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY = ROOT / "outputs/peru_secocha_boundary/peru_secocha_active_boundary.gpkg"
DATA_DIR = ROOT / "data/validation/secocha_2023_validation/rainfall/chirps_v3_daily_event_window"
OUTPUT_DIR = ROOT / "outputs/secocha_2023_validation/rainfall"
STACK_PATH = DATA_DIR / "chirps_v3_daily_2023-01-07_2023-02-10_native.tif"
ACCUM_PATH = DATA_DIR / "chirps_v3_accumulations_to_2023-02-05_native.tif"
MANIFEST_PATH = OUTPUT_DIR / "event_rainfall_manifest.json"
SUMMARY_PATH = OUTPUT_DIR / "event_rainfall_summary.json"
FIGURE_PATH = OUTPUT_DIR / "event_rainfall_accumulation.png"

BOUNDARY_ID = "peru_secocha_a7367_reference_extent_v1"
EVENT_DATE = date(2023, 2, 5)
START_DATE = date(2023, 1, 7)  # 30-day antecedent window ending on event date
END_DATE = date(2023, 2, 10)  # five post-event days for context
BUFFER_M = 5000.0
CHIRPS_PRODUCT = "sat"
VARIANT_WRAPPER_PATH: Path | None = None
CHIRPS_URL_TEMPLATE = (
    "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/{product}/{year}/"
    "chirps-v3.0.{product}.{year}.{month:02d}.{day:02d}.tif"
)
CHIRPS_DOCS = "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dates_between(start: date, end: date) -> list[date]:
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def head_metadata(url: str, context: ssl.SSLContext) -> dict[str, str | int | None]:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "IFPM-Secocha/1.0"})
    with urllib.request.urlopen(request, timeout=60, context=context) as response:
        headers = response.headers
        length = headers.get("Content-Length")
        return {
            "http_status": int(getattr(response, "status", 200)),
            "content_length_bytes": int(length) if length else None,
            "etag": headers.get("ETag"),
            "last_modified": headers.get("Last-Modified"),
            "content_type": headers.get("Content-Type"),
        }


def clean_values(array: np.ndarray) -> np.ndarray:
    """Keep CHIRPS precipitation and turn any negative sentinel into NoData."""
    result = array.astype("float32", copy=False)
    result = np.where(np.isfinite(result) & (result >= 0), result, np.float32(-9999.0))
    return result


def valid(array: np.ndarray) -> np.ndarray:
    return np.isfinite(array) & (array != -9999.0)


def write_figure(accumulations: dict[str, np.ndarray], transform: rasterio.Affine, crs: str) -> None:
    """Create a compact review figure, not a model input."""
    boundary = gpd.read_file(BOUNDARY, layer="secocha_active_boundary").to_crs(4326)
    names = list(accumulations)
    ncols = min(3, len(names))
    nrows = int(np.ceil(len(names) / ncols))
    fig, axes_grid = plt.subplots(nrows, ncols, figsize=(12, 3.8 * nrows), constrained_layout=True)
    axes = np.atleast_1d(axes_grid).ravel().tolist()
    extent = (
        transform.c,
        transform.c + transform.a * next(iter(accumulations.values())).shape[1],
        transform.f + transform.e * next(iter(accumulations.values())).shape[0],
        transform.f,
    )
    for axis, name in zip(axes, names):
        array = accumulations[name]
        image = np.ma.masked_equal(array, -9999.0)
        values = array[valid(array)]
        vmax = float(values.max()) if values.size else 1.0
        plot = axis.imshow(image, extent=extent, origin="upper", cmap="Blues", vmin=0.0, vmax=max(vmax, 1e-6))
        boundary.boundary.plot(ax=axis, color="black", linewidth=1.0)
        axis.set_title(name.replace("_", "\n"), fontsize=8)
        axis.set_xlabel("Longitude")
        axis.set_ylabel("Latitude")
        axis.xaxis.set_major_locator(MaxNLocator(nbins=3))
        axis.yaxis.set_major_locator(MaxNLocator(nbins=3))
        axis.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))
        axis.yaxis.set_major_formatter(FormatStrFormatter("%.2f"))
        axis.tick_params(axis="both", labelsize=7)
        fig.colorbar(plot, ax=axis, shrink=0.76, label="mm")
    for axis in axes[len(names):]:
        axis.set_visible(False)
    fig.suptitle("Secocha 2023 event-window rainfall (CHIRPS v3 daily; native grid)")
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_PATH, dpi=180)
    plt.close(fig)


def main() -> None:
    run_started_utc = datetime.now(timezone.utc).isoformat()
    boundary = gpd.read_file(BOUNDARY, layer="secocha_active_boundary").to_crs(32718)
    if len(boundary) != 1:
        raise RuntimeError(f"expected one active boundary, got {len(boundary)}")
    buffered = boundary.geometry.iloc[0].buffer(BUFFER_M)
    bounds_wgs84 = gpd.GeoSeries([buffered], crs=32718).to_crs(4326).total_bounds
    query_bounds = [float(value) for value in bounds_wgs84]
    run_dates = dates_between(START_DATE, END_DATE)
    context = ssl.create_default_context()

    arrays: list[np.ndarray] = []
    source_records: list[dict[str, object]] = []
    crop_window = None
    profile = None
    transform = None
    source_grid = None
    for current in run_dates:
        url = CHIRPS_URL_TEMPLATE.format(product=CHIRPS_PRODUCT, year=current.year, month=current.month, day=current.day)
        remote = head_metadata(url, context)
        vsi_url = "/vsicurl/" + url
        with rasterio.Env(
            GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
            CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
            GDAL_HTTP_USERAGENT="IFPM-Secocha/1.0",
        ):
            with rasterio.open(vsi_url) as dataset:
                if dataset.crs is None or dataset.crs.to_epsg() != 4326:
                    raise RuntimeError(f"unexpected CHIRPS CRS for {current}: {dataset.crs}")
                current_grid = (dataset.width, dataset.height, dataset.transform.a, dataset.transform.e, dataset.transform.c, dataset.transform.f)
                if not np.isclose(abs(dataset.transform.a), 0.05, atol=1e-6) or not np.isclose(abs(dataset.transform.e), 0.05, atol=1e-6):
                    raise RuntimeError(f"unexpected CHIRPS native resolution for {current}: {dataset.transform}")
                if source_grid is None:
                    source_grid = current_grid
                elif current_grid != source_grid:
                    raise RuntimeError(f"CHIRPS source grid changed on {current}: {current_grid} != {source_grid}")
                if crop_window is None:
                    crop_window = from_bounds(*query_bounds, transform=dataset.transform)
                    crop_window = crop_window.round_offsets().round_lengths()
                    if crop_window.width < 1 or crop_window.height < 1:
                        raise RuntimeError("buffered Secocha window collapsed to zero pixels")
                    profile = dataset.profile.copy()
                    transform = rasterio.windows.transform(crop_window, dataset.transform)
                current_window = crop_window
                array = clean_values(dataset.read(1, window=current_window))
                if array.shape != (int(crop_window.height), int(crop_window.width)):
                    raise RuntimeError(f"inconsistent crop shape for {current}: {array.shape}")
                arrays.append(array)
                source_records.append(
                    {
                        "date": current.isoformat(),
                        "url": url,
                        **remote,
                        "source_width": int(dataset.width),
                        "source_height": int(dataset.height),
                        "source_crs": str(dataset.crs),
                        "source_transform": [dataset.transform.a, dataset.transform.e, dataset.transform.c, dataset.transform.f],
                        "source_nodata": dataset.nodata,
                        "crop_window": {
                            "col_off": int(crop_window.col_off),
                            "row_off": int(crop_window.row_off),
                            "width": int(crop_window.width),
                            "height": int(crop_window.height),
                        },
                        "crop_min_mm": float(np.min(array[valid(array)])) if np.any(valid(array)) else None,
                        "crop_max_mm": float(np.max(array[valid(array)])) if np.any(valid(array)) else None,
                    }
                )

    assert crop_window is not None and profile is not None and transform is not None
    stack = np.stack(arrays, axis=0).astype("float32")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    stack_profile = profile.copy()
    stack_profile.update(
        driver="GTiff",
        height=stack.shape[1],
        width=stack.shape[2],
        count=stack.shape[0],
        dtype="float32",
        nodata=-9999.0,
        transform=transform,
        compress="deflate",
        predictor=2,
        tiled=False,
    )
    with rasterio.open(STACK_PATH, "w", **stack_profile) as output:
        output.write(stack)
        for index, current in enumerate(run_dates, start=1):
            output.set_band_description(index, current.isoformat())

    date_index = {current.isoformat(): index for index, current in enumerate(run_dates)}

    def range_array(start: date, end: date) -> np.ndarray:
        indices = [date_index[current.isoformat()] for current in dates_between(start, end)]
        subset = stack[indices]
        mask = valid(subset)
        return np.where(np.all(mask, axis=0), np.sum(subset, axis=0), -9999.0).astype("float32")

    accumulation_specs = {
        "cum_1d_2023-02-05": (EVENT_DATE, EVENT_DATE),
        "cum_3d_2023-02-03_2023-02-05": (date(2023, 2, 3), EVENT_DATE),
        "cum_7d_2023-01-30_2023-02-05": (date(2023, 1, 30), EVENT_DATE),
        "cum_30d_2023-01-07_2023-02-05": (START_DATE, EVENT_DATE),
        "post_5d_2023-02-06_2023-02-10": (date(2023, 2, 6), END_DATE),
    }
    accumulations = {name: range_array(start, end) for name, (start, end) in accumulation_specs.items()}
    accumulation_stack = np.stack(list(accumulations.values()), axis=0)
    accumulation_profile = stack_profile.copy()
    accumulation_profile.update(count=accumulation_stack.shape[0])
    with rasterio.open(ACCUM_PATH, "w", **accumulation_profile) as output:
        output.write(accumulation_stack)
        for index, name in enumerate(accumulations, start=1):
            output.set_band_description(index, name)

    daily_stats = []
    for current, array in zip(run_dates, arrays):
        values = array[valid(array)]
        daily_stats.append(
            {
                "date": current.isoformat(),
                "mean_mm": float(values.mean()) if values.size else None,
                "max_mm": float(values.max()) if values.size else None,
                "valid_pixels": int(values.size),
            }
        )
    accumulation_stats = {}
    for name, array in accumulations.items():
        values = array[valid(array)]
        accumulation_stats[name] = {
            "mean_mm": float(values.mean()) if values.size else None,
            "max_mm": float(values.max()) if values.size else None,
            "valid_pixels": int(values.size),
        }

    write_figure(accumulations, transform, str(profile["crs"]))
    local_files = []
    for path in (STACK_PATH, ACCUM_PATH, FIGURE_PATH):
        local_files.append(
            {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)}
        )
    manifest = {
        "dataset_id": f"secocha_2023_event_rainfall_chirps_v3_daily_{CHIRPS_PRODUCT}",
        "event_id": "secocha_2023_historical_hazard_event",
        "event_date": EVENT_DATE.isoformat(),
        "boundary_id": BOUNDARY_ID,
        "boundary_path": str(BOUNDARY.relative_to(ROOT)),
        "boundary_sha256": sha256(BOUNDARY),
        "claim_level": "validation_candidate",
        "enters_pim_score": False,
        "role": "event-trigger rainfall context; separate from the long-term PIM rainfall criterion",
        "publisher": "Climate Hazards Center, University of California Santa Barbara",
        "product": f"CHIRPS v3.0 daily final {CHIRPS_PRODUCT} 0.05-degree GeoTIFF",
        "documentation_url": CHIRPS_DOCS,
        "access_date": str(date.today()),
        "run_started_utc": run_started_utc,
        "run_finished_utc": datetime.now(timezone.utc).isoformat(),
        "implementation": {
            "base_script": str(Path(__file__).resolve().relative_to(ROOT)),
            "base_script_sha256": sha256(Path(__file__).resolve()),
            "variant_wrapper": str(VARIANT_WRAPPER_PATH.resolve().relative_to(ROOT)) if VARIANT_WRAPPER_PATH else None,
            "variant_wrapper_sha256": sha256(VARIANT_WRAPPER_PATH.resolve()) if VARIANT_WRAPPER_PATH else None,
        },
        "native_resolution": {"degrees": 0.05, "approx_km": 5.5},
        "target_grid": "native CHIRPS crop; no resampling to 30 m",
        "query_bounds_wgs84": query_bounds,
        "buffer_m": BUFFER_M,
        "date_range": {"start": START_DATE.isoformat(), "end": END_DATE.isoformat(), "days": len(run_dates)},
        "source_url_template": CHIRPS_URL_TEMPLATE,
        "source_integrity": {
            "remote_content_sha256_saved": False,
            "remote_etag_is_not_a_cryptographic_checksum": True,
            "local_crop_sha256_saved": True,
        },
        "source_files": source_records,
        "local_files": local_files,
        "stack_shape": [int(value) for value in stack.shape],
        "stack_transform": [transform.a, transform.e, transform.c, transform.f],
        "nodata_policy": "Negative/non-finite source values are stored as -9999; valid zero rainfall is retained; no imputation.",
        "daily_stats": daily_stats,
        "accumulation_stats": accumulation_stats,
        "notes": [
            "CHIRPS is a gridded precipitation product, not a local rain-gauge observation.",
            "The 0.05-degree grid is retained; the resulting pixels must not be interpreted as independent 30 m observations.",
            "Daily totals provide event-window context only; they cannot resolve the 14:00-14:17 local trigger intensity reported by INDECI.",
            "SENAMHI station/hourly data remain a separate requested source and are not silently substituted here.",
        ],
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {
        "dataset_id": manifest["dataset_id"],
        "event_date": manifest["event_date"],
        "claim_level": manifest["claim_level"],
        "rainfall_units": "mm/day and accumulated mm",
        "native_resolution": manifest["native_resolution"],
        "daily_stats": daily_stats,
        "accumulation_stats": accumulation_stats,
        "local_stack": str(STACK_PATH.relative_to(ROOT)),
        "local_accumulations": str(ACCUM_PATH.relative_to(ROOT)),
        "figure": str(FIGURE_PATH.relative_to(ROOT)),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(MANIFEST_PATH.relative_to(ROOT)), "summary": summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
