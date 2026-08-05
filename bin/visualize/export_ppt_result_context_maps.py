#!/usr/bin/env python3
"""Export legend-free, PPT-specific priority-context maps.

The figures use the current Peru and Zimbabwe PIM rasters plus the population
and mining context already governed in this workspace.  They deliberately omit
titles, legends, and explanatory text so those elements remain editable in
PowerPoint.  The map canvas follows each study area's natural aspect ratio and
adds only a small margin for the graticule, north arrow, and scale bar.
"""

from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from rasterio.features import geometry_mask


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bin/visualize"))

import export_paper_style_single_maps as maps
import export_peru_evidence_overlay_maps as peru
import export_zimbabwe_mining_population_overlay as zimbabwe


OUT_DIR = ROOT / "outputs/slide_ready_figures/ppt_result_context_maps"

PERU_PNG = OUT_DIR / "peru_priority_context_ppt.png"
PERU_PDF = PERU_PNG.with_suffix(".pdf")
ZIMBABWE_PNG = OUT_DIR / "zimbabwe_priority_context_ppt.png"
ZIMBABWE_PDF = ZIMBABWE_PNG.with_suffix(".pdf")
INDEX = OUT_DIR / "index.csv"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compact_frame_extent(
    extent: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    """Add just enough whitespace for map furniture without shrinking the map."""
    west, east, south, north = extent
    width = east - west
    height = north - south
    return (
        west - width * 0.045,
        east + width * 0.045,
        south - height * 0.085,
        north + height * 0.045,
    )


def style_map_frame(
    ax,
    site: maps.Site,
    extent: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    frame_extent = compact_frame_extent(extent)
    maps.add_boundary_and_frame(ax, site, frame_extent)
    ax.tick_params(
        top=True,
        bottom=False,
        left=True,
        right=False,
        labeltop=True,
        labelbottom=False,
        labelleft=True,
        labelright=False,
        labelsize=10.5,
        pad=2,
    )
    mid_latitude = (extent[2] + extent[3]) / 2
    ax.set_aspect(
        1 / np.cos(np.deg2rad(mid_latitude)),
        adjustable="box",
    )
    maps.add_north_arrow(ax)
    maps.add_scale_bar(ax, frame_extent)
    return frame_extent


def draw_priority_with_gap(
    ax,
    *,
    pim: Path,
    site: maps.Site,
    evidence_support: Path | None = None,
) -> tuple[tuple[float, float, float, float], float]:
    priority, profile = maps.read_raster(pim)
    classes = maps.classify_equal_interval(priority, maps.PRIORITY_BOUNDS)
    projected, extent = maps.reproject_class(classes, profile)
    masked = np.ma.masked_where(projected == 0, projected)
    cmap = ListedColormap(maps.PRIORITY_COLORS)
    norm = BoundaryNorm(
        np.arange(0.5, len(maps.PRIORITY_COLORS) + 1.5),
        len(maps.PRIORITY_COLORS),
    )
    ax.imshow(
        masked,
        extent=extent,
        origin="upper",
        cmap=cmap,
        norm=norm,
        interpolation="nearest",
        zorder=1,
    )

    if evidence_support is not None:
        support, support_profile = maps.read_raster(evidence_support)
        if support_profile != profile:
            raise ValueError("Peru evidence-support raster does not match the PIM grid")
        gap = (np.nan_to_num(support, nan=0).astype("uint8") > 1).astype("uint8")
        gap_projected, gap_extent = maps.reproject_class(gap, profile)
        if gap_extent != extent:
            raise ValueError("Peru evidence-support extent does not match the PIM extent")
    else:
        boundary = gpd.read_file(site.boundary_gpkg, layer=site.boundary_layer).to_crs(profile["crs"])
        inside = geometry_mask(
            boundary.geometry,
            out_shape=priority.shape,
            transform=profile["transform"],
            invert=True,
        )
        gap = (inside & ~np.isfinite(priority)).astype("uint8")
        gap_projected, gap_extent = maps.reproject_class(gap, profile)
        if gap_extent != extent:
            raise ValueError("Zimbabwe data-gap extent does not match the PIM extent")

    overlay = np.ma.masked_where(gap_projected != 1, gap_projected)
    ax.contourf(
        overlay,
        levels=[0.5, 1.5],
        colors="none",
        hatches=["////"],
        extent=extent,
        origin="upper",
        zorder=2,
    )
    style_map_frame(ax, site, extent)

    boundary = gpd.read_file(site.boundary_gpkg, layer=site.boundary_layer).to_crs(profile["crs"])
    inside = geometry_mask(
        boundary.geometry,
        out_shape=priority.shape,
        transform=profile["transform"],
        invert=True,
    )
    coverage = float((inside & np.isfinite(priority)).sum() / inside.sum())
    return extent, coverage


def save_figure(fig, png: Path, pdf: Path) -> None:
    # Keep the fixed canvas instead of bbox_inches='tight'.  This guarantees a
    # stable aspect ratio and prevents coordinate labels being clipped.
    fig.savefig(png, dpi=300, facecolor="white")
    fig.savefig(pdf, facecolor="white")
    plt.close(fig)


def export_peru() -> dict[str, object]:
    fig, ax = plt.subplots(figsize=(6.2, 5.2), layout="constrained")
    _, coverage = draw_priority_with_gap(
        ax,
        pim=peru.PIM,
        site=peru.SITE,
        evidence_support=peru.EVIDENCE_SUPPORT,
    )
    contour_levels = peru.draw_population_contours(ax)

    mining_records = gpd.read_file(peru.MINING).to_crs(maps.DST_CRS)
    mining_locations = peru.collapse_mining_locations(mining_records)
    boundary = gpd.read_file(peru.BOUNDARY, layer="peru_pilot_boundary").to_crs(maps.DST_CRS)
    inside_mining, _ = peru.split_locations_by_boundary(
        mining_locations,
        boundary.geometry.iloc[0],
    )
    if not inside_mining.empty:
        inside_mining.plot(
            ax=ax,
            marker="D",
            color="#111111",
            edgecolor="white",
            linewidth=0.7,
            markersize=34,
            zorder=5,
        )

    save_figure(fig, PERU_PNG, PERU_PDF)
    return {
        "site": "Peru Arequipa working study area",
        "png": rel(PERU_PNG),
        "pdf": rel(PERU_PDF),
        "pim_source": rel(peru.PIM),
        "population_source": rel(peru.POPULATION_EXPOSURE),
        "mining_source": rel(peru.MINING),
        "boundary_source": rel(peru.BOUNDARY),
        "pim_coverage_fraction": f"{coverage:.8f}",
        "population_contours": ";".join(f"{value:.2f}" for value in contour_levels),
        "mining_locations_inside_boundary": len(inside_mining),
        "claim_level": "diagnostic_only",
        "presentation_status": "prototype screening map",
        "note": "Legend-free PPT asset; titles, legend, and interpretation remain editable in PowerPoint.",
    }


def export_zimbabwe() -> dict[str, object]:
    fig, ax = plt.subplots(figsize=(5.0, 6.1), layout="constrained")
    _, coverage = draw_priority_with_gap(
        ax,
        pim=zimbabwe.PIM,
        site=zimbabwe.SITE,
    )
    contour_levels, population_valid_fraction = zimbabwe.draw_population(ax)

    mining = gpd.read_file(zimbabwe.MINING_FOOTPRINTS)
    mining = mining[mining["ISO3_CODE"].eq("ZWE")].copy()
    boundary = gpd.read_file(
        zimbabwe.BOUNDARY,
        layer="v1_working_boundary",
    ).to_crs(mining.crs)
    footprints = gpd.overlay(
        mining,
        boundary[["geometry"]],
        how="intersection",
        keep_geom_type=True,
    )
    footprints = footprints[~footprints.geometry.is_empty].copy()
    projected_footprints = footprints.to_crs(maps.DST_CRS)
    projected_footprints.plot(
        ax=ax,
        facecolor="none",
        edgecolor="white",
        linewidth=4.2,
        alpha=1.0,
        zorder=4,
    )
    projected_footprints.plot(
        ax=ax,
        facecolor="#B2188B",
        edgecolor="#65004E",
        linewidth=2.0,
        alpha=0.96,
        zorder=5,
    )

    save_figure(fig, ZIMBABWE_PNG, ZIMBABWE_PDF)
    return {
        "site": "Zimbabwe Upper Mzingwane",
        "png": rel(ZIMBABWE_PNG),
        "pdf": rel(ZIMBABWE_PDF),
        "pim_source": rel(zimbabwe.PIM),
        "population_source": rel(zimbabwe.POPULATION),
        "mining_source": rel(zimbabwe.MINING_FOOTPRINTS),
        "boundary_source": rel(zimbabwe.BOUNDARY),
        "pim_coverage_fraction": f"{coverage:.8f}",
        "population_valid_fraction": f"{population_valid_fraction:.8f}",
        "population_contours": ";".join(f"{value:.2f}" for value in contour_levels),
        "mapped_mining_footprints": len(footprints),
        "claim_level": "diagnostic_only",
        "presentation_status": "prototype screening map",
        "note": "Legend-free PPT asset; natural catchment aspect ratio retained without stretching or cropping.",
    }


def write_index(rows: list[dict[str, object]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key, value in list(row.items()):
            if not key.endswith("_source"):
                continue
            source = ROOT / str(value)
            row[f"{key.removesuffix('_source')}_sha256"] = sha256(source)
        row["png_sha256"] = sha256(ROOT / str(row["png"]))
        row["pdf_sha256"] = sha256(ROOT / str(row["pdf"]))
        for key in row:
            if key not in fields:
                fields.append(key)
    with INDEX.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    required = [
        peru.PIM,
        peru.EVIDENCE_SUPPORT,
        peru.POPULATION_EXPOSURE,
        peru.MINING,
        peru.BOUNDARY,
        zimbabwe.PIM,
        zimbabwe.POPULATION,
        zimbabwe.MINING_FOOTPRINTS,
        zimbabwe.BOUNDARY,
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing PPT-map input(s): " + ", ".join(map(str, missing)))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [export_peru(), export_zimbabwe()]
    write_index(rows)
    print(f"wrote {len(rows)} PPT-specific result maps to {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
