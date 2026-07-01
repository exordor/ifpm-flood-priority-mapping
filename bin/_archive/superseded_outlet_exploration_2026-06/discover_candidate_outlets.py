#!/usr/bin/env python3
"""Discover provisional outlet/catchment candidates from local boundary data."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import geopandas as gpd
import pandas as pd
from pyproj import Geod
from shapely.geometry import Point
from shapely.ops import nearest_points


ROOT = Path(__file__).resolve().parents[1]
HYDRO_DIR = ROOT / "data/raw/hydrosheds_zimbabwe_prototype/extracted/hybas_af_lev01-12_v1c"
GEOPORTAL = ROOT / "data/raw/zimbabwe_geoportal_subcatchments_2025/extracted/sub_catchments.shp"
OUT_DIR = ROOT / "outputs/candidate_outlet_discovery"
TODAY = date.today().isoformat()
GEOD = Geod(ellps="WGS84")
LITERATURE_AREA_KM2 = 2138.0
METRIC_CRS = "EPSG:32735"

ANCHORS = {
    "Mzingwane Dam": (28.95789, -20.38701),
    "Esigodini": (28.938056, -20.2925),
    "Gwanda": (29.0, -20.933333),
    "Filabusi approx": (29.2833, -20.5333),
    "West Nicholson approx": (29.3667, -21.05),
}

TARGETS = [
    {
        "candidate_id": "HB_L8_1081522660_literature_near",
        "source": "HydroBASINS level 8",
        "level": 8,
        "target_id": 1081522660,
        "rationale": "Upstream area is closest current HydroBASINS L8 proxy to the literature 2138 km2 reference.",
    },
    {
        "candidate_id": "HB_L8_1081528170_broader_nested",
        "source": "HydroBASINS level 8",
        "level": 8,
        "target_id": 1081528170,
        "rationale": "Broader nested L8 outlet below the upper-core branch, still inside the L7 candidate context.",
    },
    {
        "candidate_id": "HB_L8_1081520710_upper_core",
        "source": "HydroBASINS level 8",
        "level": 8,
        "target_id": 1081520710,
        "rationale": "Smaller upper-core branch containing the known upper anchor units.",
    },
    {
        "candidate_id": "HB_L8_1081528840_full_l7_chain",
        "source": "HydroBASINS level 8",
        "level": 8,
        "target_id": 1081528840,
        "rationale": "Level-8 chain representation of the full level-7 HydroBASINS candidate.",
    },
    {
        "candidate_id": "HB_L7_1071528840_primary_context",
        "source": "HydroBASINS level 7",
        "level": 7,
        "target_id": 1071528840,
        "rationale": "Previously identified strongest single HydroBASINS L7 candidate.",
    },
    {
        "candidate_id": "HB_L7_1071525530_geoportal_overlap_alt",
        "source": "HydroBASINS level 7",
        "level": 7,
        "target_id": 1071525530,
        "rationale": "Second substantial L7 overlap with the Geoportal Upper Mzingwane envelope.",
    },
]


def load_hydro(level: int) -> gpd.GeoDataFrame:
    path = HYDRO_DIR / f"hybas_af_lev{level:02d}_v1c.shp"
    return gpd.read_file(path).to_crs("EPSG:4326")


def geodesic_area_km2(geom) -> float:
    area, _ = GEOD.geometry_area_perimeter(geom)
    return abs(area) / 1_000_000


def upstream_ids(gdf: gpd.GeoDataFrame, target_id: int) -> tuple[list[int], bool, list[int]]:
    """Trace every basin upstream to ``target_id`` via the NEXT_DOWN encoding.

    Returns ``(upstream_ids, topology_ok, exited_domain_ids)``.

    In HydroBASINS, ``NEXT_DOWN=0`` marks a terminal basin and ends a trace
    normally. A trace whose ``NEXT_DOWN`` references a basin that is absent from
    the loaded set (nonzero and not present) is a domain-exit / completeness gap,
    recorded in ``exited_domain_ids`` -- distinct from a genuine cycle, which sets
    ``topology_ok=False``. Previously such domain-exits were indistinguishable from
    terminals, so a clipped or partial subset could hide missing upstream basins as
    though the trace had terminated cleanly. (The V1 prototype loads full continental
    Africa, so this branch stays empty in practice, but the distinction matters if a
    regional subset is ever used.)
    """
    next_map = dict(zip(gdf["HYBAS_ID"].astype(int), gdf["NEXT_DOWN"].astype(int)))
    ids = set(next_map)
    upstream: list[int] = []
    topology_ok = True
    exited_domain: list[int] = []
    for start in ids:
        seen: set[int] = set()
        current = start
        found_target = False
        while current in ids and current not in seen:
            if current == target_id:
                upstream.append(start)
                found_target = True
                break
            seen.add(current)
            current = next_map[current]
        if current in seen:
            topology_ok = False
            continue
        if not found_target and current != 0:
            # ``current`` is nonzero and not in ``ids``: NEXT_DOWN left the loaded
            # HydroBASINS domain (a completeness gap), not a genuine terminal.
            exited_domain.append(start)
    return sorted(upstream), topology_ok, sorted(set(exited_domain))


def check_topology_completeness(gdf: gpd.GeoDataFrame, level: int) -> None:
    """Warn about HydroBASINS NEXT_DOWN completeness gaps for one level.

    A complete continental HydroBASINS level should contain terminal basins
    (``NEXT_DOWN=0``) and have every nonzero ``NEXT_DOWN`` resolve to a basin
    present in the set. Dangling references would be expected if only a regional
    subset were loaded; the V1 prototype currently uses full continental Africa
    (0 dangling references), so this is a defensive check that must still surface
    any gap so traces are not misread as clean terminations or cycles.
    """
    next_map = dict(zip(gdf["HYBAS_ID"].astype(int), gdf["NEXT_DOWN"].astype(int)))
    ids = set(next_map)
    terminals = [hid for hid, nd in next_map.items() if nd == 0]
    dangling = sorted({nd for nd in next_map.values() if nd != 0 and nd not in ids})
    if not terminals:
        print(
            f"WARNING: HydroBASINS level {level} has no terminal basins "
            f"(NEXT_DOWN=0); the loaded shapefile may be truncated.",
            file=sys.stderr,
        )
    if dangling:
        sample = ", ".join(str(d) for d in dangling[:5])
        print(
            f"NOTE: HydroBASINS level {level}: {len(dangling)} NEXT_DOWN reference(s) "
            f"point outside the loaded set (e.g. {sample}); prototype subset, so "
            f"upstream traces may report domain-exits rather than clean terminations.",
            file=sys.stderr,
        )


def outlet_point(row, gdf: gpd.GeoDataFrame) -> tuple[Point, str]:
    target = row.geometry
    downstream_id = int(row["NEXT_DOWN"])
    downstream = gdf[gdf["HYBAS_ID"].astype(int) == downstream_id]
    if downstream.empty:
        return target.boundary.interpolate(0.5, normalized=True), "boundary_midpoint_no_downstream"
    shared = target.boundary.intersection(downstream.iloc[0].geometry.boundary)
    if not shared.is_empty and getattr(shared, "length", 0) > 0:
        return shared.interpolate(0.5, normalized=True), "shared_boundary_midpoint"
    p1, _ = nearest_points(target.boundary, downstream.iloc[0].geometry.boundary)
    return p1, "nearest_boundary_to_next_down"


def contained_anchors(geom) -> list[str]:
    return [name for name, xy in ANCHORS.items() if geom.covers(Point(*xy))]


def score_candidate(area: float, anchors: list[str], source: str, topology_ok: bool, method: str) -> dict[str, float | str]:
    hydro = 20 if source.startswith("HydroBASINS") else 8
    hydro += 7 if topology_ok else 0
    hydro += 3 if method == "shared_boundary_midpoint" else 1

    flood_raw = 0
    flood_raw += 6 if "Mzingwane Dam" in anchors else 0
    flood_raw += 5 if "Esigodini" in anchors else 0
    flood_raw += 4 if "Filabusi approx" in anchors else 0
    flood_raw += 4 if "West Nicholson approx" in anchors else 0
    flood_raw += 2 if "Gwanda" not in anchors else 0
    flood = min(flood_raw, 15)

    reproducibility = 18 if source.startswith("HydroBASINS") else 12

    consistency = 0
    consistency += 4 if "Mzingwane Dam" in anchors else 0
    consistency += 4 if "Esigodini" in anchors else 0
    consistency += 3 if "Gwanda" not in anchors else 0
    proximity = max(0, 1 - abs(area - LITERATURE_AREA_KM2) / LITERATURE_AREA_KM2)
    consistency += 4 * proximity

    if 1500 <= area <= 3000:
        parsimony = 10
    elif 1000 <= area < 1500 or 3000 < area <= 4500:
        parsimony = 7
    elif area < 1000 or area > 6000:
        parsimony = 4
    else:
        parsimony = 6

    total = hydro + flood + reproducibility + consistency + parsimony
    status = "strong_candidate" if total >= 75 else "review_candidate" if total >= 60 else "reject_or_defer"
    return {
        "hydrological_plausibility": round(hydro, 2),
        "flood_mining_relevance": round(flood, 2),
        "reproducibility": round(reproducibility, 2),
        "boundary_consistency": round(consistency, 2),
        "parsimony": round(parsimony, 2),
        "score_total": round(total, 2),
        "status": status,
    }


def build_candidates() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, pd.DataFrame, gpd.GeoDataFrame]:
    geo = gpd.read_file(GEOPORTAL).to_crs("EPSG:4326")
    upper = geo[geo["SubCatchme"] == "Upper Mzingwane"].iloc[0]
    level_cache = {7: load_hydro(7), 8: load_hydro(8)}
    for _level, _gdf in level_cache.items():
        check_topology_completeness(_gdf, _level)
    catchments = []
    outlets = []
    scores = []

    for target in TARGETS:
        gdf = level_cache[target["level"]]
        row = gdf[gdf["HYBAS_ID"].astype(int) == target["target_id"]].iloc[0]
        ids, topology_ok, exited_domain = upstream_ids(gdf, target["target_id"])
        if exited_domain:
            print(
                f"NOTE: candidate {target['candidate_id']}: {len(exited_domain)} upstream "
                f"basin(s) exit the loaded HydroBASINS L{target['level']} domain "
                f"(NEXT_DOWN references absent basins); upstream count is provisional.",
                file=sys.stderr,
            )
        catchment = gdf[gdf["HYBAS_ID"].astype(int).isin(ids)].geometry.union_all()
        point, method = outlet_point(row, gdf)
        anchors = contained_anchors(catchment)
        area = geodesic_area_km2(catchment)
        overlap = geodesic_area_km2(catchment.intersection(upper.geometry))
        score = score_candidate(area, anchors, target["source"], topology_ok, method)

        base = {
            **target,
            "target_next_down": int(row["NEXT_DOWN"]),
            "target_pf_id": int(row["PFAF_ID"]),
            "target_sub_area_km2": float(row["SUB_AREA"]),
            "target_up_area_km2": float(row["UP_AREA"]),
            "catchment_area_km2": round(area, 3),
            "geoportal_overlap_km2": round(overlap, 3),
            "geoportal_overlap_share": round(overlap / geodesic_area_km2(upper.geometry), 6),
            "candidate_overlap_share": round(overlap / area, 6),
            "upstream_unit_count": len(ids),
            "upstream_hybas_ids": ";".join(str(i) for i in ids),
            "outlet_method": method,
            "topology_ok": topology_ok,
            "topology_exited_domain_count": len(exited_domain),
            "anchors_contained": "; ".join(anchors) if anchors else "none",
            "needs_validation": "yes",
            "geometry": catchment,
        }
        catchments.append(base)
        outlets.append({k: v for k, v in base.items() if k != "geometry"} | {"geometry": point})
        scores.append({k: v for k, v in base.items() if k != "geometry"} | score)

    geo_area = geodesic_area_km2(upper.geometry)
    geo_anchors = contained_anchors(upper.geometry)
    geo_score = score_candidate(geo_area, geo_anchors, "Zimbabwe Geoportal", False, "boundary_midpoint_no_downstream")
    geo_record = {
        "candidate_id": "GEO_UPPER_MZINGWANE_management_context",
        "source": "Zimbabwe Geoportal Sub-Catchments",
        "level": "SubCatchme",
        "target_id": "Upper Mzingwane",
        "rationale": "Local named management-style envelope; comparison candidate, not hydrological acceptance.",
        "target_next_down": "",
        "target_pf_id": "",
        "target_sub_area_km2": "",
        "target_up_area_km2": "",
        "catchment_area_km2": round(geo_area, 3),
        "geoportal_overlap_km2": round(geo_area, 3),
        "geoportal_overlap_share": 1.0,
        "candidate_overlap_share": 1.0,
        "upstream_unit_count": "",
        "upstream_hybas_ids": "",
        "outlet_method": "approx_boundary_point_no_topology",
        "topology_ok": False,
        "topology_exited_domain_count": "",
        "anchors_contained": "; ".join(geo_anchors) if geo_anchors else "none",
        "needs_validation": "yes",
    }
    catchments.append(geo_record | {"geometry": upper.geometry})
    outlets.append(geo_record | {"geometry": upper.geometry.boundary.interpolate(0.5, normalized=True)})
    scores.append(geo_record | geo_score)

    catch_gdf = gpd.GeoDataFrame(catchments, geometry="geometry", crs="EPSG:4326")
    outlet_gdf = gpd.GeoDataFrame(outlets, geometry="geometry", crs="EPSG:4326")
    scoring = pd.DataFrame(scores).sort_values("score_total", ascending=False)
    search = gpd.GeoDataFrame(
        [{"name": "geoportal_hydrobasins_union_10km_buffer", "geometry": catch_gdf.geometry.union_all()}],
        crs="EPSG:4326",
    )
    search["geometry"] = search.to_crs(METRIC_CRS).buffer(10_000).to_crs("EPSG:4326")
    return catch_gdf, outlet_gdf, scoring, search


def write_outputs(catchments: gpd.GeoDataFrame, outlets: gpd.GeoDataFrame, scoring: pd.DataFrame, search: gpd.GeoDataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    scoring = scoring.copy()
    scoring.insert(0, "rank", range(1, len(scoring) + 1))
    label_map = dict(zip(scoring["candidate_id"], [f"C{i}" for i in scoring["rank"]]))
    scoring.insert(1, "plot_label", scoring["candidate_id"].map(label_map))
    catchments = catchments.copy()
    outlets = outlets.copy()
    catchments["plot_label"] = catchments["candidate_id"].map(label_map)
    outlets["plot_label"] = outlets["candidate_id"].map(label_map)

    scoring.drop(columns="geometry", errors="ignore").to_csv(OUT_DIR / "candidate_scoring.csv", index=False)
    outlets.drop(columns="geometry").assign(
        longitude=outlets.geometry.x.round(6),
        latitude=outlets.geometry.y.round(6),
        source_confidence=outlets["source"].map(lambda s: "medium" if str(s).startswith("HydroBASINS") else "low"),
    ).to_csv(OUT_DIR / "candidate_outlets.csv", index=False)
    catchments.to_file(OUT_DIR / "candidate_catchments.gpkg", layer="catchments", driver="GPKG")
    outlets.to_file(OUT_DIR / "candidate_catchments.gpkg", layer="outlets", driver="GPKG")
    search.to_file(OUT_DIR / "candidate_catchments.gpkg", layer="search_envelope", driver="GPKG")

    manifest = OUT_DIR / "source_manifest.txt"
    manifest.write_text(
        "\n".join(
            [
                f"generated={TODAY}",
                f"hydrobasins_dir={HYDRO_DIR.relative_to(ROOT)}",
                f"geoportal_subcatchments={GEOPORTAL.relative_to(ROOT)}",
                "topology_command=.venv/bin/python bin/export_candidate_topology.py",
                "plot_command=.venv/bin/python bin/plot_candidate_outlets.py",
                "new_downloads=none",
                "status=provisional; needs mentor/domain validation",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    catchments, outlets, scoring, search = build_candidates()
    write_outputs(catchments, outlets, scoring, search)
    print(scoring[["candidate_id", "catchment_area_km2", "score_total", "status"]].to_string(index=False))
    print(f"outputs written to {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
