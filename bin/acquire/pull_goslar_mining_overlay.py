#!/usr/bin/env python3
"""Build a non-scoring mining context overlay around the Goslar focus extent.

Sources:
- LBEG/NIBIS Bergwerkseigentum WFS (official mining-right polygons)
- OpenStreetMap via Overpass (mine, adit, mineshaft and quarry locations)

The overlay is context evidence only. It is not an ASM/mining-pressure score
and never enters the Goslar PIM weighted overlay.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import subprocess
import urllib.parse
from datetime import date, datetime, timezone
from pathlib import Path

import geopandas as gpd
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import polygonize, unary_union


ROOT = Path(__file__).resolve().parents[2]
DATASET_ID = "goslar_mining_context_overlay_v1"
RAW_DIR = ROOT / f"data/raw/{DATASET_ID}"
OUTPUT_DIR = ROOT / "outputs/goslar_mining_context_overlay"
OUTPUT_GPKG = OUTPUT_DIR / "goslar_mining_context_overlay.gpkg"
MANIFEST = OUTPUT_DIR / "mining_overlay_manifest.json"
BOUNDARY = ROOT / "outputs/goslar_focus_boundary/goslar_focus_boundary.gpkg"
BOUNDARY_LAYER = "goslar_focus_boundary"
METRIC_CRS = "EPSG:32632"
OVERLAY_RADIUS_M = 12_000

LBEG_WFS = "https://nibis.lbeg.de/net3/public/ogcsl.ashx"
LBEG_METADATA = "https://nibis.lbeg.de/net3/public/ogcsl.ashx?Service=Ikx&RenderHint=TargetISOWFS&NODEID=75"
LBEG_NODE_ID = "75"
LBEG_TYPENAME = "cls:L34"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def catalog() -> dict[str, object]:
    return {
        "dataset_id": DATASET_ID,
        "claim_level": "context_evidence",
        "enters_pim_score": False,
        "overlay_radius_m": OVERLAY_RADIUS_M,
        "output": "outputs/goslar_mining_context_overlay/goslar_mining_context_overlay.gpkg",
        "sources": [
            {
                "provider": "LBEG/NIBIS",
                "dataset": "Bergwerkseigentum",
                "service": "WFS 2.0, NodeId 75, cls:L34",
                "service_url": LBEG_WFS,
                "metadata_url": LBEG_METADATA,
                "licence": "CC BY 4.0",
                "required_attribution": "© GeoBasis-DE/LVermGeo SH/CC BY 4.0",
                "semantic_role": "official mining-right fields; not proof of current extraction",
            },
            {
                "provider": "OpenStreetMap/Overpass",
                "dataset": "mine, adit, mineshaft and quarry features",
                "service_url": OVERPASS_URL,
                "licence": "ODbL 1.0; © OpenStreetMap contributors",
                "semantic_role": "community-mapped point locations and area geometries",
            },
        ],
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_json(url: str, params: dict[str, str] | None = None, data: bytes | None = None) -> dict:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    command = [
        "curl", "--location", "--fail", "--silent", "--show-error",
        "--max-time", "120",
        "--user-agent", "IFPM-Goslar-mining-overlay/1.0 (research context download)",
        url,
    ]
    if data is not None:
        command.extend(["--header", "Content-Type: application/x-www-form-urlencoded", "--data-binary", "@-"])
    completed = subprocess.run(
        command,
        input=data,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace").strip())
    return json.loads(completed.stdout.decode("utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_focus():
    focus = gpd.read_file(BOUNDARY, layer=BOUNDARY_LAYER).to_crs(METRIC_CRS)
    if len(focus) != 1:
        raise ValueError(f"expected one focus feature, got {len(focus)}")
    geometry = focus.geometry.iloc[0]
    return geometry, geometry.buffer(OVERLAY_RADIUS_M)


def query_radius_for_context(focus_geometry, context_geometry) -> int:
    """Return a centroid radius guaranteed to contain the context bounds."""
    center = focus_geometry.centroid
    xmin, ymin, xmax, ymax = context_geometry.bounds
    farthest = max(
        center.distance(Point(x, y))
        for x, y in ((xmin, ymin), (xmin, ymax), (xmax, ymin), (xmax, ymax))
    )
    return int(math.ceil(farthest))


def classify_osm_tags(tags: dict[str, str]) -> str:
    """Keep specific mining meanings ahead of generic land-use tags."""
    if tags.get("man_made") in {"mine", "adit", "mineshaft"}:
        return tags["man_made"]
    if tags.get("historic") in {"mine", "mineshaft"}:
        return tags["historic"]
    if tags.get("industrial") == "mine":
        return "mine"
    if tags.get("landuse") == "quarry":
        return "quarry"
    return "mining_context"


def _coordinates(sequence: list[dict[str, float]]) -> list[tuple[float, float]]:
    return [(float(item["lon"]), float(item["lat"])) for item in sequence]


def osm_element_geometry(element: dict):
    """Convert Overpass ``out geom`` elements without collapsing areas."""
    if element.get("type") == "node" and "lat" in element and "lon" in element:
        return Point(float(element["lon"]), float(element["lat"]))
    if element.get("type") == "way" and element.get("geometry"):
        coords = _coordinates(element["geometry"])
        if len(coords) >= 4 and coords[0] == coords[-1]:
            return Polygon(coords)
        if len(coords) >= 2:
            return LineString(coords)
    if element.get("type") == "relation":
        outer_lines = []
        inner_lines = []
        for member in element.get("members", []):
            if not member.get("geometry"):
                continue
            coords = _coordinates(member["geometry"])
            if len(coords) < 2:
                continue
            line = LineString(coords)
            (inner_lines if member.get("role") == "inner" else outer_lines).append(line)
        outers = list(polygonize(unary_union(outer_lines))) if outer_lines else []
        inners = list(polygonize(unary_union(inner_lines))) if inner_lines else []
        if outers:
            geometry = unary_union(outers)
            for inner in inners:
                geometry = geometry.difference(inner)
            return geometry
    center = element.get("center", {})
    if "lat" in center and "lon" in center:
        return Point(float(center["lon"]), float(center["lat"]))
    return None


def pull_lbeg(context_geometry) -> tuple[gpd.GeoDataFrame, Path, dict[str, str]]:
    xmin, ymin, xmax, ymax = context_geometry.bounds
    params = {
        "NODEID": LBEG_NODE_ID,
        "SERVICE": "WFS",
        "VERSION": "2.0.0",
        "REQUEST": "GetFeature",
        "TYPENAMES": LBEG_TYPENAME,
        "SRSNAME": METRIC_CRS,
        "BBOX": f"{xmin},{ymin},{xmax},{ymax},{METRIC_CRS}",
        "COUNT": "10000",
        "OUTPUTFORMAT": "application/geo+json",
    }
    payload = fetch_json(LBEG_WFS, params=params)
    raw_path = RAW_DIR / "lbeg_bergwerkseigentum_12km_epsg32632.json"
    write_json(raw_path, payload)
    features = payload.get("features", [])
    if not features:
        return gpd.GeoDataFrame(columns=["geometry"], geometry="geometry", crs=METRIC_CRS), raw_path, params
    rights = gpd.GeoDataFrame.from_features(features, crs=METRIC_CRS)
    rights = rights[rights.geometry.notna() & ~rights.geometry.is_empty].copy()
    rights["source_provider"] = "LBEG/NIBIS"
    rights["source_dataset"] = "Bergwerkseigentum"
    rights["claim_level"] = "context_evidence"
    rights["enters_pim_score"] = False
    rights["geometry"] = rights.geometry.intersection(context_geometry)
    rights = rights[~rights.geometry.is_empty].copy()
    return rights, raw_path, params


def overpass_query(lat: float, lon: float, query_radius_m: int) -> str:
    return f"""[out:json][timeout:90];
(
  nwr[\"man_made\"~\"^(mine|adit|mineshaft)$\"](around:{query_radius_m},{lat},{lon});
  nwr[\"historic\"~\"^(mine|mineshaft)$\"](around:{query_radius_m},{lat},{lon});
  nwr[\"landuse\"=\"quarry\"](around:{query_radius_m},{lat},{lon});
  nwr[\"industrial\"=\"mine\"](around:{query_radius_m},{lat},{lon});
);
out body geom;"""


def pull_osm(focus_geometry, context_geometry) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, Path, str, int, str | None]:
    center = gpd.GeoSeries([focus_geometry.centroid], crs=METRIC_CRS).to_crs(4326).iloc[0]
    query_radius_m = query_radius_for_context(focus_geometry, context_geometry)
    query = overpass_query(center.y, center.x, query_radius_m)
    payload = fetch_json(
        OVERPASS_URL,
        data=urllib.parse.urlencode({"data": query}).encode("utf-8"),
    )
    raw_path = RAW_DIR / "osm_mining_features_12km.json"
    write_json(raw_path, payload)
    rows = []
    for element in payload.get("elements", []):
        geometry = osm_element_geometry(element)
        if geometry is None or geometry.is_empty:
            continue
        tags = element.get("tags", {})
        feature_type = classify_osm_tags(tags)
        rows.append(
            {
                "osm_type": element.get("type"),
                "osm_id": int(element.get("id")),
                "name": tags.get("name"),
                "feature_type": feature_type,
                "source_provider": "OpenStreetMap/Overpass",
                "claim_level": "context_evidence",
                "enters_pim_score": False,
                "matched_tag": next(
                    (f"{key}={tags[key]}" for key in ("man_made", "historic", "industrial", "landuse")
                     if classify_osm_tags({key: tags.get(key)}) != "mining_context"),
                    None,
                ),
                "osm_tags_json": json.dumps(tags, ensure_ascii=False, sort_keys=True),
                "geometry": geometry,
            }
        )
    features = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326").to_crs(METRIC_CRS)
    if len(features):
        features = features[features.geometry.intersects(context_geometry)].copy()
        features["intersects_focus_extent"] = features.geometry.intersects(focus_geometry)
        features["centroid_inside_focus"] = features.geometry.centroid.intersects(focus_geometry)
        features["distance_to_focus_m"] = features.geometry.apply(lambda geom: float(geom.distance(focus_geometry)))
        features = features.sort_values(["feature_type", "name", "osm_type", "osm_id"], na_position="last")
    points = features[features.geometry.geom_type == "Point"].copy()
    areas = features[features.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    osm_timestamp = payload.get("osm3s", {}).get("timestamp_osm_base")
    return points, areas, raw_path, query, query_radius_m, osm_timestamp


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog-only", action="store_true")
    args = parser.parse_args()
    if args.catalog_only:
        print(json.dumps(catalog(), ensure_ascii=False, indent=2))
        return 0
    if not BOUNDARY.exists():
        raise FileNotFoundError(BOUNDARY)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    focus_geometry, context_geometry = load_focus()
    rights, rights_raw, lbeg_params = pull_lbeg(context_geometry)
    osm_points, osm_areas, osm_raw, osm_query, osm_query_radius_m, osm_timestamp = pull_osm(
        focus_geometry, context_geometry
    )

    legacy_raw = RAW_DIR / "lbeg_bergwerkseigentum_12km.geojson"
    if legacy_raw.exists():
        legacy_raw.unlink()

    if OUTPUT_GPKG.exists():
        OUTPUT_GPKG.unlink()
    rights.to_file(OUTPUT_GPKG, layer="lbeg_mining_rights", driver="GPKG")
    osm_points.to_file(OUTPUT_GPKG, layer="osm_mining_points", driver="GPKG", mode="a")
    osm_areas.to_file(OUTPUT_GPKG, layer="osm_mining_areas", driver="GPKG", mode="a")

    type_counts = dict(sorted(Counter(
        [str(value) for value in osm_points["feature_type"]]
        + [str(value) for value in osm_areas["feature_type"]]
    ).items()))
    manifest = {
        **catalog(),
        "access_date": date.today().isoformat(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "focus_boundary": str(BOUNDARY.relative_to(ROOT)),
        "focus_boundary_sha256": sha256_file(BOUNDARY),
        "requests": {
            "lbeg_wfs": {
                "url": LBEG_WFS,
                "parameters": lbeg_params,
                "metadata_url": LBEG_METADATA,
                "raw_crs": METRIC_CRS,
                "count_limit": 10000,
            },
            "osm_overpass": {
                "url": OVERPASS_URL,
                "query": osm_query,
                "query_radius_m": osm_query_radius_m,
                "final_filter": "focus extent buffered by 12000 m in EPSG:32632",
                "timestamp_osm_base": osm_timestamp,
            },
        },
        "raw_files": {
            "lbeg": {"path": str(rights_raw.relative_to(ROOT)), "sha256": sha256_file(rights_raw)},
            "osm": {"path": str(osm_raw.relative_to(ROOT)), "sha256": sha256_file(osm_raw)},
        },
        "layers": {
            "lbeg_mining_rights": {
                "features": int(len(rights)),
                "intersecting_focus_extent": int(rights.geometry.intersects(focus_geometry).sum()),
                "semantic_limit": "legal mining-right fields, clipped to 12 km context; not actual disturbance footprint",
            },
            "osm_mining_points": {
                "features": int(len(osm_points)),
                "intersecting_focus_extent": int(osm_points["intersects_focus_extent"].sum()),
                "semantic_limit": "community-mapped point locations; completeness and current status are not guaranteed",
            },
            "osm_mining_areas": {
                "features": int(len(osm_areas)),
                "intersecting_focus_extent": int(osm_areas["intersects_focus_extent"].sum()),
                "feature_type_counts": type_counts,
                "semantic_limit": "community-mapped area geometry; completeness and current status are not guaranteed",
            },
        },
        "output_gpkg": {
            "path": str(OUTPUT_GPKG.relative_to(ROOT)),
            "sha256": sha256_file(OUTPUT_GPKG),
            "crs": METRIC_CRS,
        },
        "interpretation": "External mining context overlay only; excluded from Goslar PIM weights and score.",
    }
    write_json(MANIFEST, manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
