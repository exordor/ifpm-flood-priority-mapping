#!/usr/bin/env python3
"""Export the V1 working boundary package for controlled prototype use."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from textwrap import fill

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from pyproj import Geod
from shapely.geometry import Point


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs/v1_working_boundary"
OUT_GPKG = OUT_DIR / "v1_working_boundary.gpkg"
SOURCE_CATCHMENTS = ROOT / "outputs/candidate_outlet_discovery/candidate_catchments.gpkg"
VISUAL_GPKG = ROOT / "outputs/professional_outlet_review/visual_outlet_candidates.gpkg"
REVIEW_GPKG = ROOT / "outputs/professional_outlet_review/professional_outlet_review_layers.gpkg"
V1_ID = "HB_L8_1081528840_full_l7_chain"
GEOD = Geod(ellps="WGS84")

ANCHORS = {
    "Mzingwane Dam": (28.95789, -20.38701),
    "Esigodini": (28.938056, -20.2925),
    "Gwanda": (29.0, -20.933333),
    "Filabusi approx": (29.2833, -20.5333),
    "West Nicholson approx": (29.3667, -21.05),
}

ANCHOR_LABEL_OFFSETS = {
    "Mzingwane Dam": (4, 5),
    "Esigodini": (4, 5),
    "Gwanda": (5, 5),
    "Filabusi approx": (4, -12),
    "West Nicholson approx": (5, 5),
}


def geodesic_area_km2(geometry) -> float:
    area, _ = GEOD.geometry_area_perimeter(geometry)
    return abs(area) / 1_000_000


def read_layer(path: Path, layer: str) -> gpd.GeoDataFrame:
    return gpd.read_file(path, layer=layer).to_crs("EPSG:4326")


def select_v1() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    catchments = read_layer(SOURCE_CATCHMENTS, "catchments")
    v1_boundary = catchments[catchments["candidate_id"] == V1_ID].copy()
    if len(v1_boundary) != 1:
        raise ValueError(f"Expected one V1 boundary for {V1_ID}, found {len(v1_boundary)}")
    if v1_boundary.geometry.iloc[0].is_empty or not v1_boundary.geometry.iloc[0].is_valid:
        raise ValueError("V1 boundary geometry is empty or invalid")

    visual = read_layer(VISUAL_GPKG, "visual_outlet_candidates")
    v1_outlet = visual[visual["visual_id"] == "V1"].copy()
    if len(v1_outlet) != 1:
        raise ValueError(f"Expected one visual V1 outlet point, found {len(v1_outlet)}")
    return v1_boundary, v1_outlet


def anchor_checks(boundary) -> gpd.GeoDataFrame:
    rows = []
    for name, (lon, lat) in ANCHORS.items():
        point = Point(lon, lat)
        rows.append(
            {
                "anchor": name,
                "lon": lon,
                "lat": lat,
                "inside_v1": bool(boundary.covers(point)),
                "geometry": point,
            }
        )
    return gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")


def build_manifest(v1_boundary: gpd.GeoDataFrame, v1_outlet: gpd.GeoDataFrame) -> pd.DataFrame:
    boundary_row = v1_boundary.iloc[0]
    outlet_row = v1_outlet.iloc[0]
    area_check = geodesic_area_km2(boundary_row.geometry)
    return pd.DataFrame(
        [
            {
                "decision_status": "accepted_with_waiver_for_controlled_prototype",
                "final_thesis_boundary": "no",
                "visual_id": "V1",
                "candidate_id": V1_ID,
                "source": boundary_row["source"],
                "hydrobasins_level": boundary_row["level"],
                "hydrobasins_target": outlet_row["hydrobasins_target"],
                "NEXT_DOWN": outlet_row["NEXT_DOWN"],
                "catchment_area_km2": round(float(boundary_row["catchment_area_km2"]), 3),
                "geodesic_area_km2_check": round(area_check, 3),
                "crs": str(v1_boundary.crs),
                "upstream_unit_count": boundary_row["upstream_unit_count"],
                "upstream_hybas_ids": boundary_row["upstream_hybas_ids"],
                "outlet_lon": round(outlet_row.geometry.x, 6),
                "outlet_lat": round(outlet_row.geometry.y, 6),
                "machine_proxy_lon": outlet_row["machine_proxy_lon"],
                "machine_proxy_lat": outlet_row["machine_proxy_lat"],
                "snap_to_named_mzingwane_m": outlet_row["snap_to_named_mzingwane_m"],
                "mentor_feedback": "2026-06-12 thumbs-up reaction to V1 evidence board",
                "waiver_scope": "controlled prototype only; no final thesis boundary claim",
                "generated": date.today().isoformat(),
            }
        ]
    )


def write_outputs(v1_boundary: gpd.GeoDataFrame, v1_outlet: gpd.GeoDataFrame, anchors: gpd.GeoDataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if OUT_GPKG.exists():
        OUT_GPKG.unlink()

    manifest = build_manifest(v1_boundary, v1_outlet)
    manifest.to_csv(OUT_DIR / "v1_working_boundary_manifest.csv", index=False)
    anchors.drop(columns="geometry").to_csv(OUT_DIR / "v1_anchor_check.csv", index=False)

    v1_boundary.to_file(OUT_GPKG, layer="v1_working_boundary", driver="GPKG")
    v1_outlet.to_file(OUT_GPKG, layer="v1_outlet_point", driver="GPKG")
    anchors.to_file(OUT_GPKG, layer="v1_anchor_check", driver="GPKG")


def add_optional_layer(ax, layer: str, **kwargs) -> None:
    try:
        gdf = read_layer(REVIEW_GPKG, layer)
    except Exception:
        return
    if not gdf.empty:
        gdf.plot(ax=ax, **kwargs)


def plot_diagnostic(v1_boundary: gpd.GeoDataFrame, v1_outlet: gpd.GeoDataFrame, anchors: gpd.GeoDataFrame) -> None:
    other = read_layer(VISUAL_GPKG, "visual_candidate_catchments")
    c1 = other[other["candidate_id"] == "HB_L8_1081522660_literature_near"]
    v2 = other[other["candidate_id"] == "HB_L8_1081528170_broader_nested"]

    fig = plt.figure(figsize=(15, 9), constrained_layout=True)
    grid = fig.add_gridspec(1, 2, width_ratios=[1.65, 0.72])
    ax = fig.add_subplot(grid[0, 0])
    info = fig.add_subplot(grid[0, 1])
    info.axis("off")

    add_optional_layer(ax, "geoportal_upper_mzingwane", color="none", edgecolor="black", linewidth=1.3)
    add_optional_layer(ax, "geoportal_rivers", color="#1f78b4", linewidth=0.9, alpha=0.75)
    add_optional_layer(ax, "hydrorivers_review", color="#a6cee3", linewidth=0.35, alpha=0.5)
    c1.boundary.plot(ax=ax, color="#7b3294", linewidth=1.0, linestyle=":")
    v2.boundary.plot(ax=ax, color="#fdae61", linewidth=1.1, linestyle="--")
    v1_boundary.plot(ax=ax, color="#fee8c8", edgecolor="#d7191c", linewidth=2.0, alpha=0.55)
    v1_outlet.plot(ax=ax, color="#d7191c", edgecolor="white", markersize=80, zorder=10)

    for _, row in anchors.iterrows():
        color = "#238b45" if row["inside_v1"] else "#969696"
        ax.scatter(row.geometry.x, row.geometry.y, s=34, color=color, edgecolor="white", zorder=9)
        offset = ANCHOR_LABEL_OFFSETS.get(row["anchor"], (4, 3))
        ax.annotate(
            row["anchor"],
            (row.geometry.x, row.geometry.y),
            xytext=offset,
            textcoords="offset points",
            fontsize=7.6,
            bbox={"boxstyle": "round,pad=0.14", "facecolor": "white", "edgecolor": "none", "alpha": 0.78},
        )
    outlet_point = v1_outlet.geometry.iloc[0]
    ax.annotate(
        "V1 outlet proxy",
        (outlet_point.x, outlet_point.y),
        xytext=(12, 8),
        textcoords="offset points",
        fontsize=8.6,
        weight="bold",
        bbox={"boxstyle": "round,pad=0.16", "facecolor": "white", "edgecolor": "none", "alpha": 0.86},
        arrowprops={"arrowstyle": "-", "color": "#d7191c", "linewidth": 0.8},
    )

    ax.set_title("V1 working boundary map", fontsize=13, weight="bold")
    ax.set_xlabel("Longitude (EPSG:4326)")
    ax.set_ylabel("Latitude (EPSG:4326)")
    ax.grid(True, alpha=0.2)
    ax.set_aspect("equal", adjustable="box")
    ax.margins(0.04)

    handles = [
        Patch(facecolor="#fee8c8", edgecolor="#d7191c", alpha=0.55, label="V1 working boundary"),
        Line2D([0], [0], color="#fdae61", linestyle="--", label="V2 upstream alternative"),
        Line2D([0], [0], color="#7b3294", linestyle=":", label="Old C1 machine prior"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#238b45", label="Anchor inside V1"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#969696", label="Anchor outside V1"),
    ]
    info.legend(handles=handles, loc="upper left", fontsize=8.4, frameon=True, title="Legend")

    read_first = (
        "Read this first\n\n"
        "Status: accepted with waiver for controlled prototype use.\n\n"
        "This is a HydroBASINS-derived working mask, not a final thesis boundary.\n\n"
        "No SRTM, CHIRPS, AHP overlay, or flood-risk interpretation is included in this figure."
    )
    info.text(
        0.02,
        0.62,
        read_first,
        transform=info.transAxes,
        va="top",
        ha="left",
        fontsize=8.8,
        linespacing=1.35,
        bbox={"boxstyle": "round,pad=0.45", "facecolor": "#f7f7f7", "edgecolor": "#cccccc", "alpha": 0.95},
    )
    anchor_text = (
        "Anchor check\n\n"
        "Inside V1: Mzingwane Dam, Esigodini\n"
        "Outside V1: Gwanda, Filabusi approx, West Nicholson approx\n\n"
        "SRTM preflight: six planned tiles only; no DEM downloaded."
    )
    info.text(
        0.02,
        0.28,
        anchor_text,
        transform=info.transAxes,
        va="top",
        ha="left",
        fontsize=8.8,
        linespacing=1.35,
        bbox={"boxstyle": "round,pad=0.45", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.95},
    )
    fig.suptitle("V1 working boundary package: prototype-only waiver, not final thesis boundary", fontsize=14, weight="bold")
    fig.savefig(OUT_DIR / "v1_boundary_diagnostic.png", dpi=220)
    fig.savefig(OUT_DIR / "v1_boundary_diagnostic.pdf")
    plt.close(fig)


def main() -> None:
    v1_boundary, v1_outlet = select_v1()
    anchors = anchor_checks(v1_boundary.geometry.iloc[0])
    write_outputs(v1_boundary, v1_outlet, anchors)
    plot_diagnostic(v1_boundary, v1_outlet, anchors)

    manifest = pd.read_csv(OUT_DIR / "v1_working_boundary_manifest.csv")
    anchor_summary = pd.read_csv(OUT_DIR / "v1_anchor_check.csv")
    print(manifest.to_string(index=False))
    print(anchor_summary[["anchor", "inside_v1"]].to_string(index=False))
    print(f"outputs written to {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
