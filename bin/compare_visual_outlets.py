#!/usr/bin/env python3
"""Create visual outlet candidates and evidence distances for mentor review."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs/professional_outlet_review"
REVIEW_GPKG = OUT_DIR / "professional_outlet_review_layers.gpkg"
CANDIDATE_GPKG = ROOT / "outputs/candidate_outlet_discovery/candidate_catchments.gpkg"
SCORING_CSV = ROOT / "outputs/candidate_outlet_discovery/candidate_scoring.csv"
TOPOLOGY_CSV = ROOT / "outputs/candidate_outlet_discovery/candidate_topology_edges.csv"
OUT_GPKG = OUT_DIR / "visual_outlet_candidates.gpkg"
METRIC_CRS = "EPSG:32735"


def read_review(layer: str) -> gpd.GeoDataFrame:
    return gpd.read_file(REVIEW_GPKG, layer=layer).to_crs("EPSG:4326")


def nearest_distance(point: Point, gdf: gpd.GeoDataFrame) -> tuple[float | None, LineString | None]:
    if gdf.empty:
        return None, None
    point_m = gpd.GeoSeries([point], crs="EPSG:4326").to_crs(METRIC_CRS).iloc[0]
    geom_m = gdf.to_crs(METRIC_CRS).geometry.union_all()
    p1, p2 = nearest_points(point_m, geom_m)
    line = LineString([p1, p2])
    line_wgs = gpd.GeoSeries([line], crs=METRIC_CRS).to_crs("EPSG:4326").iloc[0]
    return round(p1.distance(p2), 1), line_wgs


def nearest_point(point: Point, gdf: gpd.GeoDataFrame) -> tuple[Point, float]:
    point_m = gpd.GeoSeries([point], crs="EPSG:4326").to_crs(METRIC_CRS).iloc[0]
    geom_m = gdf.to_crs(METRIC_CRS).geometry.union_all()
    p1, p2 = nearest_points(point_m, geom_m)
    snapped = gpd.GeoSeries([p2], crs=METRIC_CRS).to_crs("EPSG:4326").iloc[0]
    return snapped, round(p1.distance(p2), 1)


def named_mzingwane(osm_waterways: gpd.GeoDataFrame, geoportal_rivers: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    osm = osm_waterways[
        osm_waterways["name"].fillna("").str.lower().str.contains("mzingwane|umzingwani")
    ].copy()
    geo = geoportal_rivers[
        geoportal_rivers["NAM"].fillna("").str.lower().str.contains("mzingwane|umzingwani")
    ].copy()
    return pd.concat([osm[["geometry"]], geo[["geometry"]]], ignore_index=True).pipe(
        gpd.GeoDataFrame, geometry="geometry", crs="EPSG:4326"
    )


def mining_evidence(layers: dict[str, gpd.GeoDataFrame]) -> gpd.GeoDataFrame:
    frames = []
    for layer_name in ["osm_places", "osm_pois", "osm_landuse"]:
        gdf = layers[layer_name]
        names = gdf["name"].fillna("").str.lower() if "name" in gdf.columns else pd.Series([], dtype=str)
        fclasses = gdf["fclass"].fillna("").str.lower() if "fclass" in gdf.columns else pd.Series([], dtype=str)
        mask = names.str.contains("mine|slimes|tailing|quarr") | fclasses.str.contains("mine|quarr")
        selected = gdf[mask].copy()
        if not selected.empty:
            selected["source_layer"] = layer_name
            frames.append(selected[["source_layer", "name", "fclass", "geometry"]])
    if not frames:
        return gpd.GeoDataFrame({"source_layer": [], "name": [], "fclass": []}, geometry=[], crs="EPSG:4326")
    return gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), geometry="geometry", crs="EPSG:4326")


def gwanda_river_section(rivers: gpd.GeoDataFrame) -> Point:
    gwanda = Point(29.0, -20.933333)
    rivers_m = rivers.to_crs(METRIC_CRS).geometry.union_all()
    gwanda_m = gpd.GeoSeries([gwanda], crs="EPSG:4326").to_crs(METRIC_CRS).iloc[0]
    _, river_point = nearest_points(gwanda_m, rivers_m)
    return gpd.GeoSeries([river_point], crs=METRIC_CRS).to_crs("EPSG:4326").iloc[0]


def candidate_rows(topology: pd.DataFrame, scoring: pd.DataFrame, gwanda_section: Point) -> list[dict]:
    by_id = topology.set_index("candidate_id")
    score_by_id = scoring.set_index("candidate_id")

    def topology_candidate(label: str, linked: str, role: str, confidence: str, rationale: str) -> dict:
        edge = by_id.loc[linked]
        score = score_by_id.loc[linked]
        return {
            "visual_id": label,
            "linked_machine_candidate": linked,
            "lon": edge["outlet_lon"],
            "lat": edge["outlet_lat"],
            "candidate_type": "visual_outlet_snapped_to_named_river",
            "mentor_review_role": role,
            "confidence": confidence,
            "catchment_area_km2": score["catchment_area_km2"],
            "hydrobasins_target": edge["target_id"],
            "NEXT_DOWN": edge["NEXT_DOWN"],
            "reason": rationale,
        }

    return [
        topology_candidate(
            "V1",
            "HB_L8_1081528840_full_l7_chain",
            "recommend_for_mentor_review",
            "medium",
            "Closest current interpretation of mentor guidance: L8-based upstream chain containing Mzingwane Dam and routing down the main Mzingwane/Umzingwani channel toward Gwanda.",
        ),
        topology_candidate(
            "V2",
            "HB_L8_1081528170_broader_nested",
            "alternative_upstream_routing",
            "medium_low",
            "Intermediate downstream L8 alternative: captures reservoir influence and main-channel routing but less downstream exposure near Gwanda than V1.",
        ),
        topology_candidate(
            "V3",
            "HB_L8_1081522660_literature_near",
            "machine_prior_only",
            "low",
            "Old C1 topology prior: area is closer to the unresolved literature size, but it does not satisfy the new downstream exposure emphasis.",
        ),
        {
            "visual_id": "V4",
            "linked_machine_candidate": "",
            "lon": gwanda_section.x,
            "lat": gwanda_section.y,
            "candidate_type": "impact_river_section_not_boundary",
            "mentor_review_role": "exposure_section_reference",
            "confidence": "medium",
            "catchment_area_km2": "",
            "hydrobasins_target": "",
            "NEXT_DOWN": "",
            "reason": "Nearest mapped Mzingwane/Umzingwani river section to Gwanda; useful for downstream exposure discussion, not by itself an upstream catchment boundary.",
        },
        {
            "visual_id": "V5",
            "linked_machine_candidate": "GEO_UPPER_MZINGWANE_management_context",
            "lon": by_id.loc["GEO_UPPER_MZINGWANE_management_context", "outlet_lon"],
            "lat": by_id.loc["GEO_UPPER_MZINGWANE_management_context", "outlet_lat"],
            "candidate_type": "context_boundary_reference_not_outlet",
            "mentor_review_role": "context_only",
            "confidence": "low",
            "catchment_area_km2": score_by_id.loc["GEO_UPPER_MZINGWANE_management_context", "catchment_area_km2"],
            "hydrobasins_target": "Upper Mzingwane",
            "NEXT_DOWN": "",
            "reason": "Geoportal Upper Mzingwane management envelope; useful context but too broad and has no HydroBASINS outlet topology.",
        },
    ]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if OUT_GPKG.exists():
        OUT_GPKG.unlink()

    layers = {name: read_review(name) for name in ["geoportal_rivers", "hydrorivers_review", "osm_waterways", "osm_places", "osm_pois", "osm_landuse"]}
    rivers_named = named_mzingwane(layers["osm_waterways"], layers["geoportal_rivers"])
    mines = mining_evidence(layers)
    topology = pd.read_csv(TOPOLOGY_CSV, dtype={"NEXT_DOWN": "string"})
    scoring = pd.read_csv(SCORING_CSV)

    rows = candidate_rows(topology, scoring, gwanda_river_section(rivers_named))
    evidence_lines = []
    for row in rows:
        point = Point(float(row["lon"]), float(row["lat"]))
        row["machine_proxy_lon"] = row["lon"]
        row["machine_proxy_lat"] = row["lat"]
        row["snap_to_named_mzingwane_m"] = ""
        if row["candidate_type"] == "visual_outlet_snapped_to_named_river":
            snapped, snap_distance = nearest_point(point, rivers_named)
            row["lon"] = round(snapped.x, 6)
            row["lat"] = round(snapped.y, 6)
            row["snap_to_named_mzingwane_m"] = snap_distance
            point = Point(float(row["lon"]), float(row["lat"]))
        row["dist_to_geoportal_river_m"], line = nearest_distance(point, layers["geoportal_rivers"])
        if line:
            evidence_lines.append({"visual_id": row["visual_id"], "evidence": "nearest_geoportal_river", "geometry": line})
        row["dist_to_named_mzingwane_m"], line = nearest_distance(point, rivers_named)
        if line:
            evidence_lines.append({"visual_id": row["visual_id"], "evidence": "nearest_named_mzingwane", "geometry": line})
        row["dist_to_hydrorivers_m"], line = nearest_distance(point, layers["hydrorivers_review"])
        if line:
            evidence_lines.append({"visual_id": row["visual_id"], "evidence": "nearest_hydrorivers", "geometry": line})
        row["dist_to_osm_mining_evidence_m"], line = nearest_distance(point, mines)
        if line:
            evidence_lines.append({"visual_id": row["visual_id"], "evidence": "nearest_osm_mining", "geometry": line})

    candidates = gpd.GeoDataFrame(
        rows,
        geometry=[Point(float(row["lon"]), float(row["lat"])) for row in rows],
        crs="EPSG:4326",
    )
    candidates.to_csv(OUT_DIR / "visual_outlet_candidates.csv", index=False)
    candidates.to_file(OUT_GPKG, layer="visual_outlet_candidates", driver="GPKG")

    catchments = gpd.read_file(CANDIDATE_GPKG, layer="catchments").to_crs("EPSG:4326")
    keep = candidates["linked_machine_candidate"].replace("", pd.NA).dropna().tolist()
    catchments[catchments["candidate_id"].isin(keep)].to_file(OUT_GPKG, layer="visual_candidate_catchments", driver="GPKG")
    mines.to_file(OUT_GPKG, layer="osm_mining_evidence", driver="GPKG")
    rivers_named.to_file(OUT_GPKG, layer="named_mzingwane_rivers", driver="GPKG")
    gpd.GeoDataFrame(evidence_lines, geometry="geometry", crs="EPSG:4326").to_file(
        OUT_GPKG, layer="nearest_evidence_lines", driver="GPKG"
    )
    print(candidates.drop(columns="geometry").to_string(index=False))


if __name__ == "__main__":
    main()
