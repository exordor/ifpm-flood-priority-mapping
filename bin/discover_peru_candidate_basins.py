#!/usr/bin/env python3
"""Discover candidate HydroBASINS units intersecting the Peru Arequipa-Moquegua-Tacna envelope.

Diagnostic boundary discovery for the Peru side (IFPM-D02). Mirrors the Zimbabwe
`discover_candidate_outlets.py` logic, but reversed: Peru has no named catchment/outlet,
only three administrative departments. So this script finds HydroBASINS South America units
that intersect a discovery envelope around Arequipa+Moquegua+Tacna and reports their area,
topology, and drainage tendency (Pacific-slope vs highland).

This is `diagnostic_only`. Outputs are discovery candidates, NOT an accepted Peru boundary.
IFPM-D02 remains open until the mentor resolves the administrative-region vs
hydrographic-unit choice. No SRTM, CHIRPS, overlay, or interpretation is run.
"""

from __future__ import annotations

import csv
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from pyproj import Geod
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
HYDRO_DIR = ROOT / "data/raw/hydrosheds_peru_prototype/extracted"
OUT_DIR = ROOT / "outputs/peru_boundary_discovery"

# Discovery envelope around Arequipa, Moquegua, Tacna departments (lon/lat, EPSG:4326).
# This is a coarse rectangular proxy for the three departments, NOT an authoritative
# administrative boundary. It is used only to narrow the HydroBASINS search.
ENVELOPE = box(-73.5, -18.7, -68.8, -14.8)

# Inspected levels: coarse context (4-5) down to candidate resolution (6-8).
LEVELS = [4, 5, 6, 7, 8]

# Geod for area sanity checks (SUB_AREA/UP_AREA are in km2 in the attribute table).
GEOD = Geod(ellps="WGS84")

# Coast longitude threshold: South America Pacific coast near this region is around -71 to -72.
# Units reaching far west toward the coast are Pacific-slope; units far inland trend highland/Amazon.
PACIFIC_COAST_LON = -71.0


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def geodesic_area_km2(geom) -> float:
    return abs(GEOD.geometry_area_perimeter(geom)[0]) / 1e6


def load_level(level: int) -> gpd.GeoDataFrame:
    path = HYDRO_DIR / f"hybas_sa_lev{level:02d}_v1c.shp"
    if not path.exists():
        raise FileNotFoundError(path)
    gdf = gpd.read_file(path)
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")
    return gdf


def drainage_tendency(row) -> str:
    """Coarse drainage tendency: Pacific-slope if the unit centroid is near/below the coast longitude."""
    centroid = row.geometry.centroid
    if centroid.x <= PACIFIC_COAST_LON and centroid.y <= -16.0:
        return "pacific_slope"
    return "highland_inland"


def intersecting_units(gdf: gpd.GeoDataFrame, envelope) -> gpd.GeoDataFrame:
    hits = gdf[gdf.geometry.intersects(envelope)].copy()
    if hits.empty:
        return hits
    hits["intersect_area_km2"] = hits.geometry.apply(
        lambda g: geodesic_area_km2(g.intersection(envelope))
    )
    # Project to a metric CRS for accurate centroids, then carry lon/lat back.
    projected = hits.to_crs("EPSG:32718")  # UTM 18S covers most of southern Peru
    hits["centroid_lon"] = projected.geometry.centroid.to_crs("EPSG:4326").x.values
    hits["centroid_lat"] = projected.geometry.centroid.to_crs("EPSG:4326").y.values
    hits["drainage_tendency"] = hits.apply(drainage_tendency, axis=1)
    hits["geo_area_km2"] = hits.geometry.apply(geodesic_area_km2)
    return hits


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("(no rows)\n")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def summarize_level(level: int, hits: gpd.GeoDataFrame) -> dict[str, object]:
    if hits.empty:
        return {"level": level, "unit_count": 0, "sum_sub_area_km2": 0.0, "sum_intersect_km2": 0.0,
                "pacific_slope_count": 0, "highland_inland_count": 0}
    return {
        "level": level,
        "unit_count": int(len(hits)),
        "sum_sub_area_km2": round(float(hits["SUB_AREA"].sum()), 1),
        "sum_intersect_km2": round(float(hits["intersect_area_km2"].sum()), 1),
        "pacific_slope_count": int((hits["drainage_tendency"] == "pacific_slope").sum()),
        "highland_inland_count": int((hits["drainage_tendency"] == "highland_inland").sum()),
        "min_sub_area_km2": round(float(hits["SUB_AREA"].min()), 1),
        "max_sub_area_km2": round(float(hits["SUB_AREA"].max()), 1),
    }


def plot_discovery(level_hits: dict[int, gpd.GeoDataFrame], envelope) -> None:
    """Plot the most informative level (7) with the envelope, as a discovery diagnostic."""
    focus_level = 7
    if focus_level not in level_hits or level_hits[focus_level].empty:
        focus_level = 6
    if focus_level not in level_hits:
        return
    hits = level_hits[focus_level]
    ctx_level = 5
    context = level_hits.get(ctx_level, gpd.GeoDataFrame())

    fig, ax = plt.subplots(figsize=(9, 9), constrained_layout=True)
    if not context.empty:
        context.boundary.plot(ax=ax, color="0.8", linewidth=0.4, label=f"HydroBASINS L{ctx_level} context")
    hits.boundary.plot(ax=ax, color="tab:blue", linewidth=0.8)
    for _, r in hits.iterrows():
        c = r.geometry.centroid
        ax.text(c.x, c.y, str(int(r["HYBAS_ID"]))[-4:], fontsize=5.5, ha="center", color="navy")
    env_x, env_y = envelope.exterior.xy
    ax.plot(env_x, env_y, color="red", linewidth=1.2, linestyle="--", label="discovery envelope")
    ax.set_title(
        f"Peru boundary discovery (diagnostic_only)\n"
        f"HydroBASINS South America L{focus_level} intersecting Arequipa-Moquegua-Tacna envelope",
        fontsize=10,
    )
    ax.set_xlabel("Longitude (EPSG:4326)")
    ax.set_ylabel("Latitude")
    ax.legend(fontsize=7, loc="lower left")
    ax.grid(color="0.9", linewidth=0.4)
    ax.set_aspect("equal", adjustable="box")
    fig.savefig(OUT_DIR / "peru_boundary_discovery.png", dpi=180)
    plt.close(fig)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    level_hits: dict[int, gpd.GeoDataFrame] = {}

    for level in LEVELS:
        gdf = load_level(level)
        hits = intersecting_units(gdf, ENVELOPE)
        level_hits[level] = hits
        summaries.append(summarize_level(level, hits))
        for _, r in hits.iterrows():
            all_rows.append({
                "level": level,
                "HYBAS_ID": int(r["HYBAS_ID"]),
                "NEXT_DOWN": int(r["NEXT_DOWN"]),
                "PFAF_ID": int(r["PFAF_ID"]),
                "SUB_AREA_km2": round(float(r["SUB_AREA"]), 1),
                "UP_AREA_km2": round(float(r["UP_AREA"]), 1),
                "geo_area_km2": round(float(r["geo_area_km2"]), 1),
                "intersect_area_km2": round(float(r["intersect_area_km2"]), 1),
                "centroid_lon": round(float(r["centroid_lon"]), 3),
                "centroid_lat": round(float(r["centroid_lat"]), 3),
                "drainage_tendency": r["drainage_tendency"],
                "claim_level": "diagnostic_only",
                "note": "discovery candidate; not an accepted boundary",
            })

    write_csv(OUT_DIR / "peru_candidate_basins.csv", all_rows)
    write_csv(OUT_DIR / "peru_level_summary.csv", summaries)
    plot_discovery(level_hits, ENVELOPE)

    # Topology completeness check on the most detailed inspected level.
    finest = max(LEVELS)
    finest_gdf = load_level(finest)
    hybas_ids = set(finest_gdf["HYBAS_ID"].astype(int))
    next_downs = finest_gdf["NEXT_DOWN"].astype(int)
    terminals = int((next_downs == 0).sum())
    dangling = int(sum((nd != 0) and (nd not in hybas_ids) for nd in next_downs))

    topo = {
        "inspected_finest_level": finest,
        "total_units_at_finest": int(len(finest_gdf)),
        "terminal_units_NEXT_DOWN_0": terminals,
        "dangling_NEXT_DOWN_references": dangling,
        "topology_complete": "likely_ok" if dangling == 0 and terminals > 0 else "check_needed",
    }
    write_csv(OUT_DIR / "topology_check.csv", [topo])

    print(f"wrote Peru boundary discovery to {rel(OUT_DIR)}")
    for s in summaries:
        print(
            f"  L{s['level']}: {s['unit_count']} units, "
            f"SUB_AREA sum {s.get('sum_sub_area_km2', 0)} km2, "
            f"intersect {s.get('sum_intersect_km2', 0)} km2, "
            f"pacific {s.get('pacific_slope_count', 0)} / inland {s.get('highland_inland_count', 0)}"
        )


if __name__ == "__main__":
    main()
