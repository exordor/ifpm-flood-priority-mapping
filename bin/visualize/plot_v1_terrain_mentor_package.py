#!/usr/bin/env python3
"""Create a mentor-facing V1 terrain diagnostic figure package."""

from __future__ import annotations

import csv
import subprocess
import sys
from datetime import date
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter


ROOT = Path(__file__).resolve().parents[2]
STD_DIR = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/terrain_standardization"
OUT_DIR = ROOT / "outputs/v1_terrain_mentor_package"
GRID_GATE = ROOT / "bin/package/check_v1_raster_grid.py"
V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
NODATA = -9999.0

LAYERS = [
    {
        "key": "elevation_lowland_context",
        "title": "Elevation / lowland context",
        "path": STD_DIR / "v1_elevation_lowland_context_0_1.tif",
        "source": "v1_dem_utm35s_30m.tif",
        "direction": "Lower elevation -> higher context value",
        "role": "Context only",
        "mentor_status": "Do not use as default scoring criterion",
    },
    {
        "key": "slope_low_slope_susceptibility",
        "title": "Low-slope susceptibility candidate",
        "path": STD_DIR / "v1_slope_low_slope_susceptibility_0_1.tif",
        "source": "v1_slope_degrees_utm35s_30m.tif",
        "direction": "Lower slope -> higher diagnostic value",
        "role": "Primary terrain candidate",
        "mentor_status": "Recommended for mentor review",
    },
    {
        "key": "slope_high_runoff_pressure",
        "title": "High-slope runoff-pressure alternative",
        "path": STD_DIR / "v1_slope_high_runoff_pressure_0_1.tif",
        "source": "v1_slope_degrees_utm35s_30m.tif",
        "direction": "Higher slope -> higher diagnostic value",
        "role": "Alternative framing",
        "mentor_status": "Keep as alternative",
    },
]

BOARD_PNG = OUT_DIR / "mentor_v1_terrain_diagnostic_board.png"
BOARD_PDF = OUT_DIR / "mentor_v1_terrain_diagnostic_board.pdf"
CAPTION_MD = OUT_DIR / "mentor_v1_terrain_caption.md"
CAPTION_TXT = OUT_DIR / "mentor_v1_terrain_caption.txt"
EVIDENCE_CSV = OUT_DIR / "mentor_v1_terrain_evidence_table.csv"
GRID_CHECK = OUT_DIR / "mentor_v1_terrain_grid_check.csv"
HANDOFF = OUT_DIR / "mentor_v1_terrain_handoff.md"


plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 9.5,
        "axes.titlesize": 10.5,
        "axes.labelsize": 9,
        "legend.fontsize": 8,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def run_grid_gate() -> None:
    cmd = [sys.executable, str(GRID_GATE), "--rasters", *[str(layer["path"]) for layer in LAYERS], "--output", str(GRID_CHECK)]
    subprocess.run(cmd, cwd=ROOT, check=True)
def raster_extent(bounds) -> list[float]:
    return [bounds.left, bounds.right, bounds.bottom, bounds.top]


def km_formatter(value, _pos) -> str:
    return f"{value / 1000:.0f}"


def add_north_arrow(ax) -> None:
    ax.annotate(
        "N",
        xy=(0.08, 0.92),
        xytext=(0.08, 0.82),
        xycoords="axes fraction",
        textcoords="axes fraction",
        ha="center",
        va="center",
        fontsize=10,
        weight="bold",
        arrowprops={"arrowstyle": "-|>", "color": "#222222", "linewidth": 1.0},
    )


def add_scale_bar(ax, length_km: int = 20) -> None:
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    start_x = x0 + 0.07 * (x1 - x0)
    y = y0 + 0.075 * (y1 - y0)
    end_x = start_x + length_km * 1000
    tick_h = 0.012 * (y1 - y0)
    ax.plot([start_x, end_x], [y, y], color="#222222", linewidth=2.0, solid_capstyle="butt", zorder=12)
    ax.plot([start_x, start_x], [y - tick_h, y + tick_h], color="#222222", linewidth=0.9, zorder=12)
    ax.plot([end_x, end_x], [y - tick_h, y + tick_h], color="#222222", linewidth=0.9, zorder=12)
    ax.text((start_x + end_x) / 2, y + 1.7 * tick_h, f"{length_km} km", ha="center", va="bottom", fontsize=7.8)


def plot_panel(ax, layer: dict[str, object]) -> None:
    with rasterio.open(layer["path"]) as src:
        data = src.read(1).astype("float32")
        shown = np.where(data == src.nodata, np.nan, data)
        boundary = load_boundary(src.crs)
        img = ax.imshow(shown, cmap="viridis", extent=raster_extent(src.bounds), origin="upper", vmin=0, vmax=1)
    boundary.boundary.plot(ax=ax, color="#111111", linewidth=0.9, zorder=10)
    ax.set_title(str(layer["title"]), pad=7)
    ax.set_xlabel("Easting (km, EPSG:32735)")
    ax.set_ylabel("Northing (km, EPSG:32735)")
    ax.xaxis.set_major_formatter(FuncFormatter(km_formatter))
    ax.yaxis.set_major_formatter(FuncFormatter(km_formatter))
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.12, linewidth=0.5)
    add_north_arrow(ax)
    add_scale_bar(ax)
    return img


def plot_board() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(13.8, 5.2), constrained_layout=True)
    for ax, layer in zip(axes, LAYERS, strict=True):
        img = plot_panel(ax, layer)
        fig.colorbar(img, ax=ax, shrink=0.78, label="0-1 terrain diagnostic")
    axes[0].legend(
        handles=[Line2D([0], [0], color="#111111", linewidth=1.0, label="V1 working boundary")],
        loc="lower right",
        frameon=True,
        framealpha=0.92,
    )
    fig.savefig(BOARD_PNG)
    fig.savefig(BOARD_PDF)
    plt.close(fig)


def write_evidence_table() -> None:
    fields = [
        "layer",
        "source_raster",
        "standardization",
        "direction",
        "role",
        "mentor_review_status",
        "overlay_status",
        "limitation",
    ]
    rows = [
        {
            "layer": layer["key"],
            "source_raster": layer["source"],
            "standardization": "2nd-98th percentile clipping + min-max 0-1 scaling",
            "direction": layer["direction"],
            "role": layer["role"],
            "mentor_review_status": layer["mentor_status"],
            "overlay_status": "blocked; no AHP criteria decision",
            "limitation": "terrain-only diagnostic; not flood risk; not final thesis boundary evidence",
        }
        for layer in LAYERS
    ]
    with EVIDENCE_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def caption_text() -> str:
    return """Figure X. V1 terrain diagnostic candidates for mentor review. The maps show standardized terrain-only diagnostics within the V1 working catchment: lowland context, low-slope susceptibility, and a high-slope runoff-pressure alternative. Values are scaled from 0 to 1 using 2nd-98th percentile clipping and min-max standardization.

Source note: Terrain layers are derived from SRTMGL1 DEM preprocessing for the V1 working catchment and were checked against the V1 reference raster grid before plotting.

Interpretation note: The low-slope susceptibility layer is the primary terrain candidate for mentor review. The high-slope layer is retained as an alternative runoff-pressure framing. Elevation is context only.

Limitation note: This figure is not a flood-risk map, not an AHP-MCDA overlay, not an intervention-priority map, and not final thesis boundary evidence. CHIRPS rainfall and other criteria are not included.

Recommended in-text reference: Figure X summarizes terrain-only diagnostic candidates used to discuss how slope should be represented before any flood-risk overlay is attempted.
"""


def write_caption_and_handoff() -> None:
    caption = "# Caption: V1 Terrain Diagnostic Candidates\n\n" + caption_text()
    CAPTION_MD.write_text(caption, encoding="utf-8")
    CAPTION_TXT.write_text(caption_text(), encoding="utf-8")
    HANDOFF.write_text(
        "\n".join(
            [
                "# V1 Terrain Mentor Package Handoff",
                "",
                f"Updated: {date.today().isoformat()}",
                "",
                "Status: mentor-facing terrain diagnostic package generated from existing V1 standardized terrain rasters.",
                "",
                f"- Board PNG: `{rel(BOARD_PNG)}`",
                f"- Board PDF: `{rel(BOARD_PDF)}`",
                f"- Caption: `{rel(CAPTION_MD)}`",
                f"- Evidence table: `{rel(EVIDENCE_CSV)}`",
                f"- Grid check: `{rel(GRID_CHECK)}`",
                "",
                "Recommended question for mentor: Should the terrain component emphasize low-slope susceptibility, keep high-slope runoff pressure as an alternative, or exclude terrain from scoring until rainfall/exposure evidence is added?",
                "",
                "Scope limits: no CHIRPS, no AHP weights, no overlay, no flood-risk map, and no final thesis boundary claim.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    run_grid_gate()
    plot_board()
    write_evidence_table()
    write_caption_and_handoff()
    print(f"wrote {rel(BOARD_PNG)}")
    print(f"wrote {rel(BOARD_PDF)}")
    print(f"wrote {rel(CAPTION_MD)}")
    print(f"wrote {rel(CAPTION_TXT)}")
    print(f"wrote {rel(EVIDENCE_CSV)}")
    print(f"wrote {rel(HANDOFF)}")


if __name__ == "__main__":
    main()
