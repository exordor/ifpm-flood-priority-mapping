#!/usr/bin/env python3
"""Query SERNANP national definitive protected areas (layer 0) near Arequipa Region."""

from __future__ import annotations

import hashlib
import json
import ssl
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import geopandas as gpd
import certifi


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
OUT_DIR = ROOT / "data/raw/sernanp_peru_protected_areas"
OUT_GPKG = OUT_DIR / "peru_hybas_l7_6070641200_sernanp_protected_areas.gpkg"
MANIFEST = OUT_DIR / "query_manifest.json"
SERVICE = (
    "https://geoservicios.sernanp.gob.pe/arcgis/rest/services/"
    "servicios_ogc/peru_sernanp_0102/MapServer/0/query"
)
BUFFER_M = 5000.0

INPUTS = [BOUNDARY]
OUTPUTS = [OUT_GPKG, MANIFEST]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def buffered_bounds_wgs84() -> tuple[float, float, float, float]:
    boundary = gpd.read_file(BOUNDARY, layer="peru_pilot_boundary")
    projected = boundary.to_crs("EPSG:32718")
    buffered = gpd.GeoDataFrame(
        geometry=projected.geometry.buffer(BUFFER_M),
        crs=projected.crs,
    ).to_crs("EPSG:4326")
    return tuple(float(value) for value in buffered.total_bounds)


def query_url(bounds: tuple[float, float, float, float]) -> str:
    params = {
        "f": "geojson",
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "geometry": ",".join(f"{value:.8f}" for value in bounds),
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "outSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
    }
    return SERVICE + "?" + urllib.parse.urlencode(params)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bounds = buffered_bounds_wgs84()
    url = query_url(bounds)
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, timeout=120, context=ssl_context) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("error"):
        raise RuntimeError(f"SERNANP query failed: {payload['error']}")

    features = payload.get("features", [])
    if not features:
        raise RuntimeError("SERNANP returned no features for the buffered Arequipa Region envelope")
    protected = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
    protected = protected[protected.geometry.notna() & ~protected.geometry.is_empty].copy()
    if protected.empty:
        raise RuntimeError("SERNANP response contained no usable geometries")
    protected.to_file(OUT_GPKG, layer="sernanp_protected_areas", driver="GPKG")

    manifest = {
        "dataset_id": "sernanp_peru_protected_areas",
        "source": SERVICE.removesuffix("/query"),
        "access_date": str(date.today()),
        "query_bounds_wgs84": list(bounds),
        "query_buffer_m": BUFFER_M,
        "feature_count": int(len(protected)),
        "feature_names": sorted(
            str(value) for value in protected.get("anp_nomb", []).tolist() if value
        ),
        "output": rel(OUT_GPKG),
        "file_size_bytes": OUT_GPKG.stat().st_size,
        "sha256": sha256(OUT_GPKG),
        "claim_boundary": (
            "SERNANP national definitive protected-area layer 0 only; regional, private, "
            "and transitional layers are not queried, and this is not ecological validation."
        ),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=True), encoding="utf-8")
    print(f"wrote {len(protected)} SERNANP features to {rel(OUT_GPKG)}")


if __name__ == "__main__":
    main()
