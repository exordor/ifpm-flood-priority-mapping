#!/usr/bin/env python3
"""Export topology helper layers for candidate outlet explanation figures."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString


ROOT = Path(__file__).resolve().parents[1]
HYDRO_DIR = ROOT / "data/raw/hydrosheds_zimbabwe_prototype/extracted/hybas_af_lev01-12_v1c"
OUT_DIR = ROOT / "outputs/candidate_outlet_discovery"
GPKG = OUT_DIR / "candidate_catchments.gpkg"
SCORING = OUT_DIR / "candidate_scoring.csv"
OUTLETS = OUT_DIR / "candidate_outlets.csv"


def load_hydro(level: int, cache: dict[int, gpd.GeoDataFrame]) -> gpd.GeoDataFrame:
    if level not in cache:
        path = HYDRO_DIR / f"hybas_af_lev{level:02d}_v1c.shp"
        cache[level] = gpd.read_file(path).to_crs("EPSG:4326")
    return cache[level]


def point_xy(geom) -> tuple[float, float]:
    point = geom.representative_point()
    return round(point.x, 6), round(point.y, 6)


def export_topology() -> None:
    scoring = pd.read_csv(SCORING)
    outlets = pd.read_csv(OUTLETS)
    rows: list[dict] = []
    target_units: list[dict] = []
    downstream_units: list[dict] = []
    flow_edges: list[dict] = []
    hydro_cache: dict[int, gpd.GeoDataFrame] = {}

    for _, row in scoring.iterrows():
        outlet_row = outlets[outlets["candidate_id"] == row["candidate_id"]].iloc[0]
        record = {
            "rank": int(row["rank"]),
            "plot_label": row["plot_label"],
            "candidate_id": row["candidate_id"],
            "source": row["source"],
            "level": row["level"],
            "target_id": row["target_id"],
            "NEXT_DOWN": "",
            "catchment_area_km2": row["catchment_area_km2"],
            "score_total": row["score_total"],
            "status": row["status"],
            "outlet_lon": outlet_row["longitude"],
            "outlet_lat": outlet_row["latitude"],
            "target_centroid_lon": "",
            "target_centroid_lat": "",
            "downstream_centroid_lon": "",
            "downstream_centroid_lat": "",
            "explanation": "No HydroBASINS NEXT_DOWN topology; retained only as a management-context comparison.",
        }

        if str(row["source"]).startswith("HydroBASINS"):
            level = int(row["level"])
            target_id = int(row["target_id"])
            next_down = int(row["target_next_down"])
            record["level"] = level
            record["target_id"] = target_id
            record["NEXT_DOWN"] = str(next_down)
            hydro = load_hydro(level, hydro_cache)
            target = hydro[hydro["HYBAS_ID"].astype(int) == target_id].iloc[0]
            downstream = hydro[hydro["HYBAS_ID"].astype(int) == next_down]
            tx, ty = point_xy(target.geometry)
            record["target_centroid_lon"] = tx
            record["target_centroid_lat"] = ty
            target_units.append(
                {
                    "plot_label": row["plot_label"],
                    "candidate_id": row["candidate_id"],
                    "target_id": target_id,
                    "NEXT_DOWN": next_down,
                    "geometry": target.geometry,
                }
            )
            if not downstream.empty:
                down = downstream.iloc[0]
                dx, dy = point_xy(down.geometry)
                record["downstream_centroid_lon"] = dx
                record["downstream_centroid_lat"] = dy
                record["explanation"] = (
                    f"{row['plot_label']} is an outlet proxy: target HYBAS_ID {target_id} "
                    f"drains to NEXT_DOWN {next_down}; the upstream catchment is all same-level "
                    f"units whose downstream chain reaches {target_id}."
                )
                downstream_units.append(
                    {
                        "plot_label": row["plot_label"],
                        "candidate_id": row["candidate_id"],
                        "downstream_id": next_down,
                        "geometry": down.geometry,
                    }
                )
                flow_edges.append(
                    {
                        "plot_label": row["plot_label"],
                        "candidate_id": row["candidate_id"],
                        "target_id": target_id,
                        "NEXT_DOWN": next_down,
                        "geometry": LineString([(tx, ty), (dx, dy)]),
                    }
                )
        rows.append(record)

    pd.DataFrame(rows).to_csv(OUT_DIR / "candidate_topology_edges.csv", index=False)
    gpd.GeoDataFrame(target_units, geometry="geometry", crs="EPSG:4326").to_file(
        GPKG, layer="target_units", driver="GPKG"
    )
    gpd.GeoDataFrame(downstream_units, geometry="geometry", crs="EPSG:4326").to_file(
        GPKG, layer="downstream_units", driver="GPKG"
    )
    gpd.GeoDataFrame(flow_edges, geometry="geometry", crs="EPSG:4326").to_file(
        GPKG, layer="flow_edges", driver="GPKG"
    )
    print(f"topology helper outputs written to {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    export_topology()
