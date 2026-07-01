#!/usr/bin/env python3
"""Render reader-facing candidate outlet explanation figures."""

from __future__ import annotations

from pathlib import Path
from textwrap import fill

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs/candidate_outlet_discovery"
GPKG = OUT_DIR / "candidate_catchments.gpkg"
ANCHORS = {
    "Mzingwane Dam": (28.95789, -20.38701),
    "Esigodini": (28.938056, -20.2925),
    "Gwanda": (29.0, -20.933333),
    "Filabusi approx": (29.2833, -20.5333),
    "West Nicholson approx": (29.3667, -21.05),
}


def load_layers():
    return {
        "catchments": gpd.read_file(GPKG, layer="catchments"),
        "outlets": gpd.read_file(GPKG, layer="outlets"),
        "search": gpd.read_file(GPKG, layer="search_envelope"),
        "target_units": gpd.read_file(GPKG, layer="target_units"),
        "downstream_units": gpd.read_file(GPKG, layer="downstream_units"),
        "flow_edges": gpd.read_file(GPKG, layer="flow_edges"),
        "scoring": pd.read_csv(OUT_DIR / "candidate_scoring.csv"),
        "topology": pd.read_csv(OUT_DIR / "candidate_topology_edges.csv"),
    }


def add_anchors(ax) -> None:
    for name, xy in ANCHORS.items():
        ax.scatter(*xy, s=24, color="#f28e2b", zorder=5)
        ax.annotate(name, xy, fontsize=7, xytext=(3, 3), textcoords="offset points")


def setup_map(ax, title: str) -> None:
    ax.set_title(title)
    ax.set_xlabel("Longitude (EPSG:4326)")
    ax.set_ylabel("Latitude (EPSG:4326)")
    ax.grid(True, alpha=0.25)


def save(fig, name: str) -> None:
    if not fig.get_constrained_layout():
        fig.tight_layout()
    fig.savefig(OUT_DIR / f"{name}.png", dpi=220)
    fig.savefig(OUT_DIR / f"{name}.pdf")
    plt.close(fig)


def draw_overview(layers) -> None:
    catchments = layers["catchments"]
    outlets = layers["outlets"]
    search = layers["search"]
    scoring = layers["scoring"]

    primary = catchments[catchments["plot_label"] == "C1"]
    fig = plt.figure(figsize=(14, 8), constrained_layout=True)
    grid = fig.add_gridspec(1, 2, width_ratios=[1.1, 1])
    ax = fig.add_subplot(grid[0, 0])
    info = fig.add_subplot(grid[0, 1])
    info.axis("off")

    search.boundary.plot(ax=ax, color="#777777", linewidth=1, linestyle="--")
    catchments.boundary.plot(ax=ax, color="#2f80c0", linewidth=1)
    primary.plot(ax=ax, color="#a7d5f2", alpha=0.35, edgecolor="#005f99", linewidth=2)
    catchments[catchments["candidate_id"].str.startswith("GEO_")].boundary.plot(
        ax=ax, color="#111111", linewidth=1.6
    )
    outlets.plot(ax=ax, color="#6a3d9a", edgecolor="white", markersize=45, zorder=6)
    add_anchors(ax)
    for _, row in outlets.iterrows():
        ax.annotate(str(row["plot_label"]), (row.geometry.x, row.geometry.y), fontsize=8, weight="bold")
    setup_map(ax, "Candidate outlets overview\nAll points are outlet proxies, not measured outlets")

    read_first = (
        "Read this first:\n"
        "1. Purple C-points are outlet proxies from HydroBASINS topology.\n"
        "2. Blue boundaries are candidate upstream catchments.\n"
        "3. Black boundary is the broader Geoportal Upper Mzingwane context.\n"
        "4. Orange points are sanity-check anchors, not validation data.\n"
        "5. No river lines, DEM, mining, or flood-zone evidence is used yet."
    )
    top_rows = scoring.head(4)
    summary = "\n".join(
        f"{r.plot_label}: {r.candidate_id}\n  area={r.catchment_area_km2:.1f} km2, score={r.score_total:.2f}, {r.status}"
        for r in top_rows.itertuples()
    )
    legend = (
        "Legend:\n"
        "light blue fill = C1 former machine-prior catchment\n"
        "blue lines = candidate catchment boundaries\n"
        "black line = Geoportal management context\n"
        "gray dashed line = search envelope\n"
        "purple points = outlet proxy locations"
    )
    info.text(
        0,
        1,
        f"{read_first}\n\nTop ranked candidates:\n{summary}\n\n{legend}",
        va="top",
        ha="left",
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.55", "facecolor": "#f7f7f7", "edgecolor": "#cccccc"},
    )
    save(fig, "diagnostic_map_explained")

    # Preserve the legacy file names as the upgraded overview figure.
    fig = plt.figure(figsize=(15, 9))
    ax = fig.add_subplot(111)
    search.boundary.plot(ax=ax, color="#777777", linewidth=1, linestyle="--")
    catchments.boundary.plot(ax=ax, color="#2f80c0", linewidth=1)
    primary.plot(ax=ax, color="#a7d5f2", alpha=0.35, edgecolor="#005f99", linewidth=2)
    catchments[catchments["candidate_id"].str.startswith("GEO_")].boundary.plot(
        ax=ax, color="#111111", linewidth=1.6
    )
    outlets.plot(ax=ax, color="#6a3d9a", edgecolor="white", markersize=45, zorder=6)
    add_anchors(ax)
    for _, row in outlets.iterrows():
        ax.annotate(str(row["plot_label"]), (row.geometry.x, row.geometry.y), fontsize=8, weight="bold")
    setup_map(ax, "Candidate outlets overview\nDiagnostic only - not accepted boundary")
    save(fig, "diagnostic_map")


def draw_c1_explainer(layers) -> None:
    catchments = layers["catchments"]
    outlets = layers["outlets"]
    targets = layers["target_units"]
    downstreams = layers["downstream_units"]
    flow_edges = layers["flow_edges"]
    topology = layers["topology"]
    c1 = topology[topology["plot_label"] == "C1"].iloc[0]

    fig = plt.figure(figsize=(15, 9))
    grid = fig.add_gridspec(1, 2, width_ratios=[1.55, 1])
    ax = fig.add_subplot(grid[0, 0])
    info = fig.add_subplot(grid[0, 1])
    info.axis("off")

    catchments[catchments["plot_label"] == "C1"].plot(ax=ax, color="#bfe3f7", edgecolor="#005f99", linewidth=2)
    downstreams[downstreams["plot_label"] == "C1"].plot(ax=ax, color="#d9d9d9", edgecolor="#666666", linewidth=1.5)
    targets[targets["plot_label"] == "C1"].plot(ax=ax, color="#1565c0", alpha=0.65, edgecolor="#08306b", linewidth=2)
    outlets[outlets["plot_label"] == "C1"].plot(ax=ax, color="#6a3d9a", edgecolor="white", markersize=70, zorder=8)
    add_anchors(ax)

    edge = flow_edges[flow_edges["plot_label"] == "C1"].iloc[0].geometry
    start = edge.coords[0]
    end = edge.coords[-1]
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops={"arrowstyle": "->", "linewidth": 2.4, "color": "#c0392b"},
        zorder=9,
    )
    ax.annotate("flow direction: target basin -> NEXT_DOWN basin", xy=end, fontsize=8, color="#c0392b")
    setup_map(ax, "C1 outlet proxy\nTarget basin drains to NEXT_DOWN basin")

    analogy = "\n".join(
        [
            "Programming analogy:",
            "HydroBASINS polygon = graph node",
            "NEXT_DOWN = directed edge to the downstream node",
            "Upstream catchment = all nodes that eventually flow into the target node",
        ]
    )
    c1_next_down = c1["NEXT_DOWN"]
    facts = "\n".join(
        [
            f"C1 target HYBAS_ID: {int(c1.target_id)}",
            f"C1 NEXT_DOWN: {int(c1_next_down)}",
            "C1 outlet proxy: boundary point between target and downstream",
            f"C1 upstream catchment area: {c1.catchment_area_km2:.1f} km2",
            f"C1 score: {c1.score_total:.2f}",
        ]
    )
    colors = "\n".join(
        [
            "Color key:",
            "light blue = C1 upstream catchment",
            "dark blue = target basin",
            "gray = NEXT_DOWN downstream basin",
            "purple dot = outlet proxy",
            "red arrow = topology flow direction",
        ]
    )
    limits = fill(
        "Important limits: This is not a measured river outlet. It is generated from "
        "HydroBASINS NEXT_DOWN topology. No river line, DEM flow accumulation, mining "
        "footprint, or flood-zone evidence has been used yet.",
        width=70,
    )
    explanation = f"{analogy}\n\n{facts}\n\n{colors}\n\n{limits}"
    info.text(
        0,
        1,
        explanation,
        va="top",
        ha="left",
        fontsize=10,
        bbox={"boxstyle": "round,pad=0.55", "facecolor": "#f7f7f7", "edgecolor": "#cccccc"},
    )
    save(fig, "diagnostic_c1_flow_explainer")


def draw_topology_table(layers) -> None:
    scoring = layers["scoring"]
    topology = layers["topology"].set_index("candidate_id")
    rows = []
    for row in scoring.itertuples():
        edge = topology.loc[row.candidate_id]
        target = str(edge.target_id) if pd.notna(edge.target_id) and str(edge.target_id) != "nan" else "n/a"
        next_down_value = edge["NEXT_DOWN"]
        next_down = (
            str(int(next_down_value))
            if pd.notna(next_down_value) and str(next_down_value) != "nan"
            else "n/a"
        )
        rows.append(
            [
                row.plot_label,
                f"{target} -> {next_down}",
                f"{row.catchment_area_km2:.1f}",
                fill(str(row.anchors_contained), width=22),
                f"{row.score_total:.2f}",
                row.status,
            ]
        )

    fig, ax = plt.subplots(figsize=(16, 10))
    ax.axis("off")
    ax.set_title("Topology table: why the C-points are outlet proxies", fontsize=16, pad=16)
    intro = (
        "Each HydroBASINS candidate uses target_id -> NEXT_DOWN as a directed edge. "
        "The outlet proxy is placed at the target/downstream boundary. "
        "Geoportal C7 has no HydroBASINS topology and is only a management-context comparison."
    )
    ax.text(0.02, 0.92, fill(intro, width=150), fontsize=10, transform=ax.transAxes)
    table = ax.table(
        cellText=rows,
        colLabels=["Label", "target_id -> NEXT_DOWN", "Area km2", "Anchors covered", "Score", "Status"],
        cellLoc="left",
        colLoc="left",
        loc="center",
        colWidths=[0.07, 0.23, 0.09, 0.28, 0.08, 0.18],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 2.0)
    for (r, _c), cell in table.get_celld().items():
        if r == 0:
            cell.set_facecolor("#d9eaf7")
            cell.set_text_props(weight="bold")
            cell.set_height(0.06)
        elif r == 1:
            cell.set_facecolor("#eef7fd")
            cell.set_height(0.085)
        else:
            cell.set_height(0.085)
    save(fig, "diagnostic_topology_table")


def main() -> None:
    layers = load_layers()
    draw_overview(layers)
    draw_c1_explainer(layers)
    draw_topology_table(layers)


if __name__ == "__main__":
    main()
