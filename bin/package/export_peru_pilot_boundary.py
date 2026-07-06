#!/usr/bin/env python3
"""Export the southern Peru comparison-catchment boundary package.

This boundary is HydroBASINS L7 HYBAS_ID=6070641200 in Arequipa Region, mainly
the Vitor-La Joya-Santa Rita de Siguas area west of Arequipa city. It is a
provisional comparison catchment selected by an explicit rule, not a final
research-selected Peru study area. It exists to run the Peru terrain chain
end-to-end and prove comparability with Zimbabwe. It will be replaced if the
mentor later names a specific Peru site.

Mirrors `export_v1_working_boundary.py` but single-source (one HydroBASINS polygon, no outlet
discovery layers, no anchors because no mentor-named Peru places exist).
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from pyproj import Geod

ROOT = Path(__file__).resolve().parents[2]
INPUTS = [ROOT / "data/raw/hydrosheds_peru_prototype/extracted/hybas_sa_lev07_v1c.shp"]
OUTPUTS = [ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"]
OUT_DIR = ROOT / "outputs/peru_pilot_boundary"
OUT_GPKG = OUT_DIR / "peru_pilot_boundary.gpkg"

HYDRO_L7 = ROOT / "data/raw/hydrosheds_peru_prototype/extracted/hybas_sa_lev07_v1c.shp"

# Southern Peru comparison catchment. Selection rule documented in DECISION_LOG.md.
PILOT_HYBAS_ID = 6070641200
PILOT_LABEL = "PE1_HYBAS_L7_6070641200_arequipa_vitor_lajoya_siguas"

GEOD = Geod(ellps="WGS84")


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def geodesic_area_km2(geometry) -> float:
    area, _ = GEOD.geometry_area_perimeter(geometry)
    return abs(area) / 1e6


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    gdf = gpd.read_file(HYDRO_L7)
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")

    hit = gdf[gdf["HYBAS_ID"] == PILOT_HYBAS_ID]
    if hit.empty:
        raise SystemExit(f"HYBAS_ID {PILOT_HYBAS_ID} not found in {rel(HYDRO_L7)}")
    row = hit.iloc[0]

    geom = row.geometry
    geo_area = geodesic_area_km2(geom)
    bounds = [round(float(x), 5) for x in geom.bounds]

    # Build the boundary GeoDataFrame with provenance fields.
    boundary = gpd.GeoDataFrame(
        [{
            "boundary_id": PILOT_LABEL,
            "source": "HydroBASINS South America standard v1c, level 7",
            "HYBAS_ID": int(row["HYBAS_ID"]),
            "PFAF_ID": int(row["PFAF_ID"]),
            "NEXT_DOWN": int(row["NEXT_DOWN"]),
            "SUB_AREA_km2": float(row["SUB_AREA"]),
            "UP_AREA_km2": float(row["UP_AREA"]),
            "geo_area_km2": round(geo_area, 3),
            "crs_source": "EPSG:4326",
            "status": "provisional_comparison_catchment_not_final_study_area",
            "claim_level": "diagnostic_only",
        }],
        geometry=[geom],
        crs="EPSG:4326",
    )

    # Manifest CSV (mirrors Zimbabwe v1_working_boundary_manifest.csv style).
    manifest = [{
        "field": k,
        "value": v if not isinstance(v, float) else round(v, 6),
    } for k, v in boundary.drop(columns="geometry").iloc[0].items()]
    manifest.append({"field": "bounds_wsen", "value": bounds})
    manifest.append({"field": "export_date", "value": str(date.today())})
    manifest.append({"field": "zimbabwe_v1_area_reference_km2", "value": 3689.484})
    manifest.append({"field": "area_ratio_pe1_to_zw_v1", "value": round(geo_area / 3689.484, 4)})

    with (OUT_DIR / "peru_pilot_boundary_manifest.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["field", "value"])
        w.writeheader()
        w.writerows(manifest)

    # Anchor check: nearest known department capitals (discovery references, NOT accepted anchors).
    from shapely.geometry import Point
    refs = {
        "Arequipa city (ref)": Point(-71.5375, -16.3989),
        "Moquegua city (ref)": Point(-70.9347, -17.1956),
        "Tacna city (ref)": Point(-70.2806, -18.0147),
    }
    anchor_rows = []
    for name, pt in refs.items():
        # geodesic distance from point to the nearest point on the polygon boundary
        nearest = geom.exterior.interpolate(geom.exterior.project(pt)) if geom.exterior else geom.representative_point()
        d_km = abs(GEOD.inv(pt.x, pt.y, nearest.x, nearest.y)[2]) / 1e3
        anchor_rows.append({
            "reference_point": name,
            "lon": round(pt.x, 5),
            "lat": round(pt.y, 5),
            "inside_boundary": bool(geom.contains(pt) or geom.touches(pt)),
            "nearest_boundary_distance_km": round(d_km, 2),
            "note": "department-capital reference for orientation; not an accepted anchor",
        })
    with (OUT_DIR / "peru_pilot_anchor_check.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(anchor_rows[0].keys()))
        w.writeheader()
        w.writerows(anchor_rows)

    boundary.to_file(OUT_GPKG, layer="peru_pilot_boundary", driver="GPKG")

    # Diagnostic map.
    fig, ax = plt.subplots(figsize=(7, 7), constrained_layout=True)
    boundary.boundary.plot(ax=ax, color="tab:red", linewidth=1.4, label="Arequipa Region comparison catchment")
    boundary.plot(ax=ax, color="tab:red", alpha=0.12)
    for r in anchor_rows:
        ax.plot(r["lon"], r["lat"], "k^", markersize=6)
        ax.annotate(r["reference_point"].replace(" (ref)", ""), (r["lon"], r["lat"]),
                    fontsize=7, xytext=(4, 4), textcoords="offset points")
    c = geom.centroid
    ax.text(c.x, c.y, "Vitor-La Joya-Siguas", fontsize=9, ha="center", fontweight="bold", color="darkred")
    ax.set_title(
        f"Southern Peru Comparison Catchment\n"
        f"HydroBASINS Level 7 | {geo_area:.0f} km2 | Pacific-slope catchment | diagnostic map",
        fontsize=9,
    )
    ax.set_xlabel("Longitude (EPSG:4326)")
    ax.set_ylabel("Latitude")
    ax.legend(fontsize=7, loc="lower left")
    ax.grid(color="0.9", linewidth=0.4)
    ax.set_aspect("equal", adjustable="box")
    fig.savefig(OUT_DIR / "peru_pilot_boundary_diagnostic.png", dpi=180)
    plt.close(fig)

    print(f"wrote southern Peru comparison catchment PE1 to {rel(OUT_DIR)}")
    print(f"  HYBAS_ID={PILOT_HYBAS_ID}, geo_area={geo_area:.1f} km2 "
          f"(ZW V1 ref 3689.5, ratio {geo_area/3689.484:.2f})")
    print(f"  bounds WSEN: {bounds}")


if __name__ == "__main__":
    main()
