#!/usr/bin/env python3
"""Plot a paper/report-ready Upper Mzingwane boundary map and save caption files."""

from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pyogrio.errors
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from pyproj import Geod

# pyogrio (the geopandas default backend) raises DataLayerError for a layer that is
# absent from a *present* file; a missing file or a corrupt layer raises
# DataSourceError and is left to propagate. fiona signals a missing layer with a
# plain ValueError, which is too broad to catch safely, so there is no portable
# cross-backend tuple -- we rely on the pyogrio backend. (geopandas >= 1.0 defaults
# to pyogrio; if a non-pyogrio backend is ever forced, an absent optional layer will
# raise loudly instead of being skipped.)
LAYER_MISSING = (pyogrio.errors.DataLayerError,)


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/v1_working_boundary"
V1_GPKG = OUT_DIR / "v1_working_boundary.gpkg"
# Archived 2026-07-02: see outputs/_archive/superseded_outlet_exploration_2026-06/.
REVIEW_GPKG = ROOT / "outputs/_archive/superseded_outlet_exploration_2026-06/professional_outlet_review/professional_outlet_review_layers.gpkg"
FIG_BASE = OUT_DIR / "v1_boundary_paper"
GEOD = Geod(ellps="WGS84")

ANCHOR_LABEL_OFFSETS = {
    "Mzingwane Dam": (5, -2),
    "Esigodini": (5, 4),
    "Gwanda": (5, -10),
    "Filabusi approx": (5, -10),
    "West Nicholson approx": (5, 4),
}

CAPTION = """# Caption: Upper Mzingwane Prototype Catchment Boundary

Figure X. Working catchment boundary for the Upper Mzingwane prototype, derived from HydroBASINS Level-8 topology. The boundary includes Mzingwane Dam and Esigodini and follows the main Mzingwane/Umzingwani river corridor downstream toward Gwanda, while Gwanda lies outside the working catchment. The reference outlet point is shown as the downstream point used for data preparation.

Source note: HydroBASINS Level-8 is used for the working catchment boundary; Zimbabwe Geoportal and river layers are shown as contextual reference layers.

Boundary note: This boundary is accepted with waiver for controlled prototype use and should not be described as the final thesis boundary unless separately confirmed.

Recommended in-text reference: Figure X shows the working catchment boundary used to define the spatial mask for the Upper Mzingwane prototype.
"""


def read_layer(path: Path, layer: str) -> gpd.GeoDataFrame:
    return gpd.read_file(path, layer=layer).to_crs("EPSG:4326")


def add_context_layer(ax, layer: str, **kwargs) -> None:
    try:
        gdf = read_layer(REVIEW_GPKG, layer)
    except LAYER_MISSING:
        print(f"layer '{layer}' not present in {REVIEW_GPKG.name}; skipping", file=sys.stderr)
        return
    if not gdf.empty:
        gdf.plot(ax=ax, **kwargs)


def load_inputs() -> dict[str, gpd.GeoDataFrame]:
    return {
        "v1": read_layer(V1_GPKG, "v1_working_boundary"),
        "outlet": read_layer(V1_GPKG, "v1_outlet_point"),
        "anchors": read_layer(V1_GPKG, "v1_anchor_check"),
        "geoportal": read_layer(REVIEW_GPKG, "geoportal_upper_mzingwane"),
    }


def add_anchor_labels(ax, anchors: gpd.GeoDataFrame) -> None:
    for _, row in anchors.iterrows():
        color = "#009E73" if bool(row["inside_v1"]) else "#7A7A7A"
        ax.scatter(row.geometry.x, row.geometry.y, s=26, color=color, edgecolor="white", linewidth=0.6, zorder=9)
        ax.annotate(
            row["anchor"],
            (row.geometry.x, row.geometry.y),
            xytext=ANCHOR_LABEL_OFFSETS.get(row["anchor"], (5, 4)),
            textcoords="offset points",
            fontsize=7.4,
            bbox={"boxstyle": "round,pad=0.11", "facecolor": "white", "edgecolor": "none", "alpha": 0.78},
            zorder=10,
        )


def add_outlet_label(ax, outlet: gpd.GeoDataFrame) -> None:
    point = outlet.geometry.iloc[0]
    ax.scatter(point.x, point.y, s=56, color="#D55E00", edgecolor="white", linewidth=0.7, zorder=11)
    ax.annotate(
        "Reference outlet point",
        (point.x, point.y),
        xytext=(9, 7),
        textcoords="offset points",
        fontsize=7.8,
        weight="bold",
        bbox={"boxstyle": "round,pad=0.12", "facecolor": "white", "edgecolor": "none", "alpha": 0.82},
        arrowprops={"arrowstyle": "-", "color": "#D55E00", "linewidth": 0.7},
        zorder=12,
    )


def add_north_arrow(ax) -> None:
    ax.annotate(
        "N",
        xy=(0.07, 0.94),
        xytext=(0.07, 0.84),
        xycoords="axes fraction",
        textcoords="axes fraction",
        ha="center",
        va="center",
        fontsize=11,
        weight="bold",
        arrowprops={"arrowstyle": "-|>", "color": "#222222", "linewidth": 1.1},
    )


def add_scale_bar(ax, length_km: int = 20) -> None:
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    lat = y0 + 0.08 * (y1 - y0)
    start_lon = x0 + 0.08 * (x1 - x0)
    end_lon, _, _ = GEOD.fwd(start_lon, lat, 90, length_km * 1000)
    ax.plot([start_lon, end_lon], [lat, lat], color="#222222", linewidth=2.2, solid_capstyle="butt", zorder=12)
    tick_h = 0.008 * (y1 - y0)
    ax.plot([start_lon, start_lon], [lat - tick_h, lat + tick_h], color="#222222", linewidth=1.1, zorder=12)
    ax.plot([end_lon, end_lon], [lat - tick_h, lat + tick_h], color="#222222", linewidth=1.1, zorder=12)
    ax.text((start_lon + end_lon) / 2, lat + 1.8 * tick_h, f"{length_km} km", ha="center", va="bottom", fontsize=7.8)


def add_legend(ax) -> None:
    handles = [
        Patch(facecolor="#F6E8C3", edgecolor="#D55E00", alpha=0.62, label="Prototype catchment"),
        Line2D([0], [0], color="#111111", linewidth=1.1, label="Geoportal context boundary"),
        Line2D([0], [0], color="#0072B2", linewidth=0.9, label="River/stream"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#D55E00", label="Reference outlet point"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#009E73", label="Anchor inside prototype catchment"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#7A7A7A", label="Anchor outside prototype catchment"),
    ]
    ax.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        fontsize=7.6,
        frameon=True,
        framealpha=0.94,
        borderpad=0.5,
    )


def plot_paper_map() -> None:
    data = load_inputs()
    fig, ax = plt.subplots(figsize=(6.9, 7.6), constrained_layout=True)

    add_context_layer(ax, "hydrorivers_review", color="#B9DFF1", linewidth=0.3, alpha=0.45)
    add_context_layer(ax, "geoportal_rivers", color="#0072B2", linewidth=0.75, alpha=0.78)
    data["geoportal"].boundary.plot(ax=ax, color="#111111", linewidth=1.1)
    data["v1"].plot(ax=ax, color="#F6E8C3", edgecolor="#D55E00", linewidth=1.6, alpha=0.62)
    add_anchor_labels(ax, data["anchors"])
    add_outlet_label(ax, data["outlet"])

    minx, miny, maxx, maxy = data["geoportal"].total_bounds
    pad_x = (maxx - minx) * 0.06
    pad_y = (maxy - miny) * 0.06
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)

    add_north_arrow(ax)
    add_scale_bar(ax, length_km=20)
    add_legend(ax)

    ax.set_xlabel("Longitude (EPSG:4326)")
    ax.set_ylabel("Latitude (EPSG:4326)")
    ax.grid(True, alpha=0.16, linewidth=0.6)
    ax.set_aspect("equal", adjustable="box")
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)

    fig.savefig(FIG_BASE.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(FIG_BASE.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def write_caption() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "v1_boundary_paper_caption.md").write_text(CAPTION, encoding="utf-8")
    plain = CAPTION.replace("# Caption: Upper Mzingwane Prototype Catchment Boundary\n\n", "")
    (OUT_DIR / "v1_boundary_paper_caption.txt").write_text(plain, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plot_paper_map()
    write_caption()
    print(f"wrote {FIG_BASE.with_suffix('.png').relative_to(ROOT)}")
    print(f"wrote {FIG_BASE.with_suffix('.pdf').relative_to(ROOT)}")
    print("wrote outputs/v1_working_boundary/v1_boundary_paper_caption.md")
    print("wrote outputs/v1_working_boundary/v1_boundary_paper_caption.txt")


if __name__ == "__main__":
    main()
