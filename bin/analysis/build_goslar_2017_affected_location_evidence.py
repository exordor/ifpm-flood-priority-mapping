#!/usr/bin/env python3
"""Build location-based Goslar 2017 historical-event consistency evidence.

The output represents sourced affected-place samples, not a complete inundation
footprint. It samples the current provisional PIM without changing model weights.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.ticker import StrMethodFormatter
from pyproj import Transformer
from shapely.geometry import Point
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/validation/goslar_2017_affected_locations_v1/source_locations.json"
PIM = ROOT / "outputs/srtm_1arcsec_goslar/priority_scenarios/scenarios/priority_goslar_direct_pim.tif"
OUT = ROOT / "outputs/goslar_2017_affected_location_evidence"
GPKG = OUT / "goslar_2017_affected_location_evidence.gpkg"
CSV = OUT / "affected_location_pim_samples.csv"
SUMMARY = OUT / "location_consistency_summary.json"
FIGURE = OUT / "goslar_2017_affected_locations_vs_pim.png"
MANIFEST = OUT / "manifest.json"
CONFIG = Path(__file__).with_name("goslar_2017_location_diagnostics.json")
HIGH_THRESHOLD = 0.60
VERY_HIGH_THRESHOLD = 0.80


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_text(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def pim_class(value: float) -> str:
    if value >= VERY_HIGH_THRESHOLD:
        return "Very High"
    if value >= HIGH_THRESHOLD:
        return "High"
    if value >= 0.40:
        return "Moderate"
    if value >= 0.20:
        return "Moderate-Low"
    return "Low"


def evidence_group(evidence_type: str) -> str:
    if "evacuation" in evidence_type:
        return "Evacuation location"
    if evidence_type == "infrastructure_damage":
        return "Infrastructure damage"
    if evidence_type == "priority_response_reach":
        return "Affected river/street reach reference"
    return "Confirmed affected location"


def sample_pim(records: list[dict]) -> tuple[gpd.GeoDataFrame, dict]:
    with rasterio.open(PIM) as dataset:
        if dataset.crs is None:
            raise ValueError("PIM raster has no CRS")
        raster = dataset.read(1, masked=True)
        values = raster.filled(np.nan).astype("float64")
        valid = np.isfinite(values)
        high = valid & (values >= HIGH_THRESHOLD)
        if not high.any():
            raise ValueError("PIM contains no cells at or above the declared High threshold")

        transformer = Transformer.from_crs("EPSG:4326", dataset.crs, always_xy=True)
        high_rows, high_cols = np.where(high)
        high_x, high_y = rasterio.transform.xy(dataset.transform, high_rows, high_cols, offset="center")
        high_x = np.asarray(high_x)
        high_y = np.asarray(high_y)
        half_pixel_x = abs(dataset.res[0]) * 0.5
        half_pixel_y = abs(dataset.res[1]) * 0.5
        output_crs = dataset.crs

        rows: list[dict] = []
        geometries: list[Point] = []
        for record in records:
            x, y = transformer.transform(record["longitude"], record["latitude"])
            row, col = dataset.index(x, y)
            if not (0 <= row < dataset.height and 0 <= col < dataset.width):
                raise ValueError(f"location outside PIM grid: {record['location_id']}")
            value = float(values[row, col])
            if not np.isfinite(value):
                raise ValueError(f"location has no valid PIM support: {record['location_id']}")

            dx = np.maximum(np.abs(high_x - x) - half_pixel_x, 0.0)
            dy = np.maximum(np.abs(high_y - y) - half_pixel_y, 0.0)
            distance_to_high = float(np.min(np.hypot(dx, dy)))
            distance_to_high_rounded = float(round(distance_to_high / 10.0) * 10.0)

            radius_cells = int(np.ceil(100.0 / min(abs(dataset.res[0]), abs(dataset.res[1]))))
            r0, r1 = max(0, row - radius_cells), min(dataset.height, row + radius_cells + 1)
            c0, c1 = max(0, col - radius_cells), min(dataset.width, col + radius_cells + 1)
            rr, cc = np.mgrid[r0:r1, c0:c1]
            xx, yy = rasterio.transform.xy(dataset.transform, rr, cc, offset="center")
            xx = np.asarray(xx).reshape(rr.shape)
            yy = np.asarray(yy).reshape(rr.shape)
            within = (xx - x) ** 2 + (yy - y) ** 2 <= 100.0**2
            local_values = values[r0:r1, c0:c1]
            supported = within & np.isfinite(local_values)
            max_100m = float(np.max(local_values[supported])) if supported.any() else value

            source = record["source"]
            rows.append(
                {
                    "location_id": record["location_id"],
                    "location_name": record["location_name"],
                    "event_date": "2017-07-26",
                    "evidence_type": record["evidence_type"],
                    "evidence_group": evidence_group(record["evidence_type"]),
                    "impact_summary": record["impact_summary"],
                    "source_org": source["organisation"],
                    "source_url": source["url"],
                    "source_locator": source["locator"],
                    "coordinate_source": record["coordinate_source"],
                    "position_precision": record["position_precision"],
                    "longitude": record["longitude"],
                    "latitude": record["latitude"],
                    "pim_value": round(value, 6),
                    "pim_cell_id": f"{row}:{col}",
                    "pim_class": pim_class(value),
                    "distance_to_high_m": distance_to_high_rounded,
                    "distance_method": "approximate point-to-High-cell footprint distance; rounded to 10 m",
                    "max_pim_100m": round(max_100m, 6),
                    "within_100m_of_high": bool(max_100m >= HIGH_THRESHOLD),
                    "enters_pim_score": False,
                    "claim_level": "validation_candidate",
                }
            )
            geometries.append(Point(x, y))

        profile = {
            "crs": str(dataset.crs),
            "width": dataset.width,
            "height": dataset.height,
            "resolution": [abs(dataset.res[0]), abs(dataset.res[1])],
            "nodata": dataset.nodata,
            "transform": list(dataset.transform)[:6],
        }
    return gpd.GeoDataFrame(rows, geometry=geometries, crs=output_crs), profile


def write_diagnostics(points):
    """Descriptive sensitivity, with equal reach weights and explicit background support."""
    config = json.loads(CONFIG.read_text())
    assignments = config["reach_groups"]
    if not assignments or any(not v for v in assignments.values()):
        raise ValueError("Reach groups must be nonempty")
    if not config["radii_m"] or any(not np.isfinite(r) or r < 0 for r in config["radii_m"]) or config["local_background_radius_m"] <= 0:
        raise ValueError("Invalid diagnostic radii")
    lookup = {member: key for key, members in assignments.items() for member in members}
    members = [m for group in assignments.values() for m in group]
    if len(members) != len(set(members)) or set(members) != set(points.location_id):
        raise ValueError("Reach groups must partition the location catalog exactly")
    points["reach_group"] = points.location_id.map(lookup)
    with rasterio.open(PIM) as ds:
        if not ds.crs.is_projected or ds.crs.linear_units != "metre" or ds.transform.b or ds.transform.d:
            raise ValueError("Diagnostics require an unrotated projected metre grid")
        values = ds.read(1, masked=True).filled(float("nan"))
        valid = np.isfinite(values)
        rr, cc = np.where(valid)
        xx, yy = rasterio.transform.xy(ds.transform, rr, cc)
        background_xy = np.column_stack([xx, yy])
        high_xy = background_xy[values[rr, cc] >= HIGH_THRESHOLD]
        if not len(high_xy):
            raise ValueError("No High cells")
        tree = cKDTree(high_xy)
        bg_distance = tree.query(background_xy)[0]
        point_xy = np.column_stack([points.geometry.x, points.geometry.y])
        point_distance = tree.query(point_xy)[0]
        # Radius 0 samples the containing cell; positive radii query cell centres.
        local = cKDTree(point_xy).query(background_xy)[0] <= config["local_background_radius_m"]
        detail, comparison = [], []
        for radius in config["radii_m"]:
            hits = (points.pim_class.isin(["High", "Very High"]).to_numpy()
                    if radius == 0 else point_distance <= radius)
            bg_hits = bg_distance <= radius
            for i, row in enumerate(points.itertuples()):
                detail.append(dict(location_id=row.location_id, evidence_type=row.evidence_type,
                    reach_group=row.reach_group, radius_m=radius, high_present=bool(hits[i])))
            groups = {"all_records": np.ones(len(points), dtype=bool)}
            groups.update({"evidence:"+kind: (points.evidence_type == kind).to_numpy() for kind in sorted(set(points.evidence_type))})
            groups.update({"reach:"+key: (points.reach_group == key).to_numpy() for key in assignments})
            for key, mask in groups.items():
                comparison.append(dict(group=key, radius_m=radius, records=int(mask.sum()),
                    high_present_count=int(hits[mask].sum()), high_present_fraction=float(hits[mask].mean())))
            cell_hits = points[["reach_group", "pim_cell_id"]].copy()
            cell_hits["hit"] = hits.astype(float)
            reach_mean = float(cell_hits.groupby(["reach_group", "pim_cell_id"])["hit"].mean().groupby("reach_group").mean().mean())
            comparison.append(dict(group="equal_weight_reach_mean", radius_m=radius, records=len(assignments),
                high_present_count="", high_present_fraction=reach_mean))
            for name, mask in [("background_all_valid",np.ones(len(rr),dtype=bool)), ("background_locations_1km",local)]:
                if not mask.any():
                    raise ValueError("Empty background")
                comparison.append(dict(group=name, radius_m=radius, records=int(mask.sum()),
                    high_present_count=int(bg_hits[mask].sum()), high_present_fraction=float(bg_hits[mask].mean())))
    files = {}
    for name, rows in [("radius_location_samples",detail),("radius_group_background_comparison",comparison)]:
        path = OUT / (name + ".csv")
        with path.open("w", newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
        files[name] = {"path":str(path.relative_to(ROOT)),"sha256":sha256(path)}
    files["diagnostic_config"] = {"path":str(CONFIG.relative_to(ROOT)),"sha256":sha256(CONFIG)}
    return files, config


def write_figure(points: gpd.GeoDataFrame) -> None:
    with rasterio.open(PIM) as dataset:
        data = dataset.read(1, masked=True)
        margin = 650.0
        minx, miny, maxx, maxy = points.total_bounds
        left, right = minx - margin, maxx + margin
        bottom, top = miny - margin, maxy + margin
        window = rasterio.windows.from_bounds(left, bottom, right, top, dataset.transform)
        window = window.round_offsets().round_lengths()
        cropped = dataset.read(1, window=window, masked=True)
        transform = dataset.window_transform(window)
        extent = (
            transform.c,
            transform.c + transform.a * cropped.shape[1],
            transform.f + transform.e * cropped.shape[0],
            transform.f,
        )

    colors = ["#ffffcc", "#ffeda0", "#feb24c", "#f03b20", "#bd0026"]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm([0, 0.2, 0.4, 0.6, 0.8, 1.0], cmap.N)
    fig = plt.figure(figsize=(16, 10), constrained_layout=True)
    grid = fig.add_gridspec(1, 2, width_ratios=[2.7, 1.3])
    ax = fig.add_subplot(grid[0, 0])
    side = fig.add_subplot(grid[0, 1])
    image = ax.imshow(cropped, extent=extent, origin="upper", cmap=cmap, norm=norm, interpolation="nearest")
    ax.contour(
        np.asarray(cropped.filled(np.nan)),
        levels=[HIGH_THRESHOLD],
        colors=["#7f0000"],
        linewidths=1.2,
        extent=extent,
        origin="upper",
    )
    ax.scatter(
        points.geometry.x,
        points.geometry.y,
        s=110,
        c="#1565c0",
        edgecolors="white",
        linewidths=1.5,
        zorder=4,
    )
    for index, row in points.reset_index(drop=True).iterrows():
        offsets = {1: (0, 13), 2: (30, -6), 4: (31, 13), 5: (28, -23), 8: (20, 31)}
        offset = offsets.get(index, (0, 0))
        ax.annotate(str(index + 1), xy=(row.geometry.x, row.geometry.y),
            xytext=offset, textcoords="offset points", ha="center", va="center",
            color="white", fontsize=8.5, fontweight="bold", zorder=5,
            bbox=dict(boxstyle="circle,pad=0.2", fc="#1565c0", ec="white"),
            arrowprops=dict(arrowstyle="-", color="#1565c0") if offset != (0, 0) else None)

    ax.set_title(
        "Goslar 2017 flood impacts and response locations",
        loc="left",
        fontsize=18,
        fontweight="bold",
        y=1.065,
        pad=0,
    )
    ax.text(
        0,
        1.01,
        "Location-based historical-event consistency check — not a flood-extent validation",
        transform=ax.transAxes,
        fontsize=11,
        color="#555555",
    )
    ax.set_xlabel("Easting (m), EPSG:32632")
    ax.set_ylabel("Northing (m), EPSG:32632")
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:.0f}"))
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:.0f}"))
    ax.grid(color="white", linewidth=0.4, alpha=0.45)
    colorbar = fig.colorbar(image, ax=ax, fraction=0.034, pad=0.02, ticks=[0.1, 0.3, 0.5, 0.7, 0.9])
    colorbar.ax.set_yticklabels(["0.0–0.2", "0.2–0.4", "0.4–0.6", "0.6–0.8", "0.8–1.0"])
    colorbar.set_label("Relative flood-priority index")

    side.axis("off")
    side.set_title("Reported locations (approximate)", loc="left", fontsize=14, fontweight="bold", pad=12)
    y = 0.96
    for index, row in points.reset_index(drop=True).iterrows():
        text = (
            f"{index + 1}. {row.location_name}\n"
            f"PIM {row.pim_value:.3f} · {row.pim_class} · nearest High {row.distance_to_high_m:.0f} m"
        )
        side.text(0.0, y, text, transform=side.transAxes, va="top", fontsize=10.2, linespacing=1.35)
        y -= 0.09
    side.text(
        0.0,
        0.06,
        "Interpretation\nBlue markers show reported impacts and response locations. Street and square coordinates are approximate reference positions. The dark-red contour marks PIM ≥ 0.60. The samples are incomplete and cannot support IoU, recall or false-positive-area metrics.",
        transform=side.transAxes,
        va="bottom",
        fontsize=9.4,
        color="#444444",
        wrap=True,
        bbox={"boxstyle": "round,pad=0.6", "facecolor": "#f3f4f6", "edgecolor": "#d1d5db"},
    )
    temporary = FIGURE.with_suffix(".part.png")
    fig.savefig(temporary, dpi=180, facecolor="white")
    plt.close(fig)
    os.replace(temporary, FIGURE)


def main() -> int:
    source_payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    locations = source_payload["locations"]
    if len(locations) != 9 or len({row["location_id"] for row in locations}) != 9:
        raise ValueError("source catalog must contain exactly nine unique location records")
    sources = source_payload["sources"]
    records = [{**row, "source": sources[row["source_id"]]} for row in locations]
    OUT.mkdir(parents=True, exist_ok=True)

    points, raster_profile = sample_pim(records)
    diagnostic_files, diagnostic_config = write_diagnostics(points)
    temporary_gpkg = GPKG.with_suffix(".part.gpkg")
    if temporary_gpkg.exists():
        temporary_gpkg.unlink()
    points.to_file(temporary_gpkg, layer="affected_location_evidence", driver="GPKG")
    os.replace(temporary_gpkg, GPKG)

    csv_rows = points.drop(columns="geometry").to_dict(orient="records")
    temporary_csv = CSV.with_suffix(".part.csv")
    with temporary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    os.replace(temporary_csv, CSV)

    write_figure(points)
    class_counts = points["pim_class"].value_counts().to_dict()
    summary = {
        "dataset_id": source_payload["dataset_id"],
        "validation_type": "location_based_historical_event_consistency_check",
        "status": "provisional",
        "claim_level": "validation_candidate",
        "classification_policy": {
            "low": [0.0, 0.2],
            "moderate_low": [0.2, 0.4],
            "moderate": [0.4, HIGH_THRESHOLD],
            "high": [HIGH_THRESHOLD, VERY_HIGH_THRESHOLD],
            "very_high": [VERY_HIGH_THRESHOLD, 1.0],
            "interval_rule": "lower bound inclusive; upper bound exclusive except 1.0",
        },
        "high_threshold": HIGH_THRESHOLD,
        "very_high_threshold": VERY_HIGH_THRESHOLD,
        "sample_count": len(points),
        "valid_pim_sample_count": int(points["pim_value"].notna().sum()),
        "class_counts": class_counts,
        "high_or_very_high_sample_count": int(points["pim_class"].isin(["High", "Very High"]).sum()),
        "within_100m_of_high_count": int(points["within_100m_of_high"].sum()),
        "mean_pim": round(float(points["pim_value"].mean()), 6),
        "median_pim": round(float(points["pim_value"].median()), 6),
        "interpretation": "Descriptive spatial consistency only. Official affected-place samples are incomplete, positionally approximate and not a complete flood footprint; this result neither validates the PIM nor justifies weight changes.",
        "prohibited_metrics": [
            "flood_extent_recall",
            "flooded_nonflooded_accuracy",
            "intersection_over_union",
            "false_positive_flood_area",
        ],
    }
    atomic_text(SUMMARY, json.dumps(summary, indent=2, ensure_ascii=False) + "\n")

    generated = datetime.now(timezone.utc).isoformat()
    manifest = {
        "dataset_id": source_payload["dataset_id"],
        "generated_utc": generated,
        "status": "provisional",
        "claim_level": "validation_candidate",
        "validation_type": "location_based_historical_event_consistency_check",
        "event_window": source_payload["event_window"],
        "event_peak_date": source_payload["event_peak_date"],
        "location_count": len(points),
        "enters_pim_score": False,
        "is_complete_flood_extent": False,
        "weights_changed": False,
        "classification_policy": {
            "low": [0.0, 0.2],
            "moderate_low": [0.2, 0.4],
            "moderate": [0.4, HIGH_THRESHOLD],
            "high": [HIGH_THRESHOLD, VERY_HIGH_THRESHOLD],
            "very_high": [VERY_HIGH_THRESHOLD, 1.0],
            "interval_rule": "lower bound inclusive; upper bound exclusive except 1.0",
        },
        "high_threshold": HIGH_THRESHOLD,
        "very_high_threshold": VERY_HIGH_THRESHOLD,
        "coordinate_method": source_payload["coordinate_method"],
        "source_catalog": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha256(SOURCE)},
        "pim_raster": {"path": str(PIM.relative_to(ROOT)), "sha256": sha256(PIM), **raster_profile},
        "diagnostics": {"status": "diagnostic_only", **diagnostic_config},
        "outputs": {
            **diagnostic_files,
            "gpkg": {"path": str(GPKG.relative_to(ROOT)), "sha256": sha256(GPKG)},
            "csv": {"path": str(CSV.relative_to(ROOT)), "sha256": sha256(CSV)},
            "summary": {"path": str(SUMMARY.relative_to(ROOT)), "sha256": sha256(SUMMARY)},
            "figure": {"path": str(FIGURE.relative_to(ROOT)), "sha256": sha256(FIGURE)},
        },
        "limitations": [
            "Records mix reported flood impacts, evacuations and response locations; no unaffected controls.",
            "Street, square and reach coordinates are representative OSM reference positions rather than exact damaged parcels.",
            "The evidence cannot support flood-extent accuracy, recall, IoU or false-positive-area metrics.",
            "The current PIM is sampled with frozen weights; using this event to tune weights would make it calibration evidence.",
        ],
    }
    atomic_text(MANIFEST, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
