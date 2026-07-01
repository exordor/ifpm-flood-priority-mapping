#!/usr/bin/env python3
"""Plot mentor-facing professional outlet visual review board."""

from __future__ import annotations

from pathlib import Path
from textwrap import fill

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs/professional_outlet_review"
REVIEW_GPKG = OUT_DIR / "professional_outlet_review_layers.gpkg"
VISUAL_GPKG = OUT_DIR / "visual_outlet_candidates.gpkg"

ANCHORS = {
    "Mzingwane Dam": (28.95789, -20.38701),
    "Esigodini": (28.938056, -20.2925),
    "Gwanda": (29.0, -20.933333),
    "Filabusi approx": (29.2833, -20.5333),
    "West Nicholson approx": (29.3667, -21.05),
}


def layer(name: str, source: Path = REVIEW_GPKG) -> gpd.GeoDataFrame:
    return gpd.read_file(source, layer=name).to_crs("EPSG:4326")


def setup(ax, title: str) -> None:
    ax.set_title(title, fontsize=12, weight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, alpha=0.18)
    ax.set_aspect("equal", adjustable="box")


def add_anchors(ax, names: list[str] | None = None) -> None:
    selected = names or list(ANCHORS)
    for name in selected:
        x, y = ANCHORS[name]
        ax.scatter(x, y, s=24, color="#f28e2b", zorder=8)
        ax.annotate(name, (x, y), xytext=(4, 3), textcoords="offset points", fontsize=7)


def add_visual_labels(ax, candidates: gpd.GeoDataFrame) -> None:
    colors = {"V1": "#d7191c", "V2": "#fdae61", "V3": "#7b3294", "V4": "#2c7bb6", "V5": "#999999"}
    for _, row in candidates.iterrows():
        ax.scatter(row.geometry.x, row.geometry.y, s=54, color=colors.get(row.visual_id, "black"), edgecolor="white", zorder=10)
        ax.annotate(row.visual_id, (row.geometry.x, row.geometry.y), xytext=(4, 4), textcoords="offset points", fontsize=9, weight="bold")


def add_context(ax, layers: dict[str, gpd.GeoDataFrame]) -> None:
    layers["review_envelope"].boundary.plot(ax=ax, color="#777777", linestyle="--", linewidth=1)
    layers["geoportal_upper_mzingwane"].boundary.plot(ax=ax, color="black", linewidth=1.6)


def draw_overview(ax, layers: dict[str, gpd.GeoDataFrame], candidates: gpd.GeoDataFrame, catchments: gpd.GeoDataFrame) -> None:
    add_context(ax, layers)
    layers["geoportal_rivers"].plot(ax=ax, color="#005f99", linewidth=1.2, alpha=0.75)
    layers["osm_waterways"].plot(ax=ax, color="#9ecae1", linewidth=0.45, alpha=0.45)
    catchments[catchments["candidate_id"].str.contains("1081528840", na=False)].plot(
        ax=ax, color="#fee8c8", edgecolor="#e34a33", alpha=0.38, linewidth=1.8
    )
    catchments[catchments["candidate_id"].str.contains("1081528170", na=False)].boundary.plot(
        ax=ax, color="#fdae61", linewidth=1.3
    )
    catchments[catchments["candidate_id"].str.contains("1081522660", na=False)].boundary.plot(
        ax=ax, color="#7b3294", linewidth=1.1
    )
    layers["machine_outlets"].plot(ax=ax, color="#6b6b6b", markersize=15, alpha=0.55)
    add_visual_labels(ax, candidates)
    add_anchors(ax)
    setup(ax, "A. Visual outlet candidates and machine priors")


def draw_river_evidence(ax, layers: dict[str, gpd.GeoDataFrame], candidates: gpd.GeoDataFrame) -> None:
    add_context(ax, layers)
    layers["hydrorivers_review"].plot(ax=ax, color="#9ecae1", linewidth=0.55, alpha=0.55, label="HydroRIVERS")
    layers["geoportal_rivers"].plot(ax=ax, color="#005f99", linewidth=1.4, alpha=0.85, label="Geoportal Rivers")
    layer("named_mzingwane_rivers", VISUAL_GPKG).plot(ax=ax, color="#08306b", linewidth=2.0, alpha=0.8, label="Named Mzingwane/Umzingwani")
    layer("nearest_evidence_lines", VISUAL_GPKG).plot(ax=ax, color="#d73027", linewidth=0.7, alpha=0.45)
    add_visual_labels(ax, candidates[candidates["visual_id"].isin(["V1", "V2", "V3", "V4"])])
    setup(ax, "B. River evidence and snapped visual points")
    ax.legend(loc="lower left", fontsize=7)


def draw_impact_evidence(ax, layers: dict[str, gpd.GeoDataFrame], candidates: gpd.GeoDataFrame) -> None:
    add_context(ax, layers)
    layers["osm_roads"].plot(ax=ax, color="#bdbdbd", linewidth=0.35, alpha=0.55)
    layers["geoportal_rivers"].plot(ax=ax, color="#005f99", linewidth=1.0, alpha=0.7)
    mines = layer("osm_mining_evidence", VISUAL_GPKG)
    if not mines.empty:
        mines.representative_point().plot(ax=ax, color="#a50f15", marker="^", markersize=55, label="OSM mine/quarry evidence")
        labelled = set()
        for _, row in mines.iterrows():
            point = row.geometry.representative_point()
            label = str(row.get("name") or row.get("fclass") or "mine")
            if label and label.lower() not in {"nan", "quarry"} and label not in labelled:
                ax.annotate(label[:22], (point.x, point.y), xytext=(3, 2), textcoords="offset points", fontsize=6)
                labelled.add(label)
    add_visual_labels(ax, candidates[candidates["visual_id"].isin(["V1", "V4"])])
    add_anchors(ax, ["Mzingwane Dam", "Gwanda", "Filabusi approx", "West Nicholson approx"])
    setup(ax, "C. Exposure and mining-context clues")
    ax.text(
        0.02,
        0.02,
        "Geoportal Flood Prone Zones: 0 features intersect review envelope",
        transform=ax.transAxes,
        fontsize=8,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
    )


def draw_decision_panel(ax, candidates: gpd.GeoDataFrame) -> None:
    ax.axis("off")
    role_labels = {
        "recommend_for_mentor_review": "primary review",
        "alternative_upstream_routing": "upstream alt",
        "machine_prior_only": "machine prior",
        "exposure_section_reference": "impact reach",
        "context_only": "context only",
    }
    rows = []
    for _, row in candidates.iterrows():
        rows.append(
            [
                row.visual_id,
                role_labels.get(row.mentor_review_role, row.mentor_review_role),
                f"{float(row.catchment_area_km2):.1f}" if pd.notna(row.catchment_area_km2) and str(row.catchment_area_km2) else "",
                f"{row.snap_to_named_mzingwane_m}" if str(row.snap_to_named_mzingwane_m) else "n/a",
                fill(str(row.reason), 62),
            ]
        )
    table = ax.table(
        cellText=rows,
        colLabels=["ID", "Role", "Area km2", "Snap m", "Reason"],
        colWidths=[0.06, 0.15, 0.10, 0.08, 0.61],
        loc="center",
        cellLoc="left",
        colLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7)
    table.scale(1, 2.65)
    for (r, c), cell in table.get_celld().items():
        if r == 0:
            cell.set_facecolor("#deebf7")
            cell.set_text_props(weight="bold")
        elif r == 1:
            cell.set_facecolor("#fee8c8")
    ax.set_title("D. Mentor decision summary: C1 demoted, V1 goes to review", fontsize=12, weight="bold")


def main() -> None:
    layers = {
        name: layer(name)
        for name in [
            "review_envelope",
            "geoportal_upper_mzingwane",
            "geoportal_rivers",
            "hydrorivers_review",
            "osm_waterways",
            "osm_roads",
            "machine_outlets",
        ]
    }
    candidates = layer("visual_outlet_candidates", VISUAL_GPKG)
    catchments = layer("visual_candidate_catchments", VISUAL_GPKG)

    fig = plt.figure(figsize=(18, 13), constrained_layout=True)
    grid = fig.add_gridspec(2, 2)
    draw_overview(fig.add_subplot(grid[0, 0]), layers, candidates, catchments)
    draw_river_evidence(fig.add_subplot(grid[0, 1]), layers, candidates)
    draw_impact_evidence(fig.add_subplot(grid[1, 0]), layers, candidates)
    draw_decision_panel(fig.add_subplot(grid[1, 1]), candidates)
    fig.suptitle(
        "Professional outlet visual review: visual candidates, not accepted boundary\n"
        "Mentor cue: Level-8 basin containing Mzingwane Dam and main Mzingwane River channel downstream toward Gwanda",
        fontsize=15,
        weight="bold",
    )
    fig.savefig(OUT_DIR / "mentor_outlet_evidence_board.png", dpi=220)
    fig.savefig(OUT_DIR / "mentor_outlet_evidence_board.pdf")
    plt.close(fig)


if __name__ == "__main__":
    main()
