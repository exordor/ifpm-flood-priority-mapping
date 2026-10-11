#!/usr/bin/env python3
"""Acquire the original INGEMMET A7367 hazard polygons around Secocha."""

from __future__ import annotations

import hashlib
import json
import ssl
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import certifi
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[2]
BOUNDARY = ROOT / "outputs/secocha_boundary/secocha_boundary.gpkg"
OUT_DIR = ROOT / "data/raw/ingemmet_a7367_cartografia_peligros_secocha"
OUT_PATH = OUT_DIR / "ingemmet_a7367_cartografia_peligros_layer6_secocha.geojson"
MANIFEST = ROOT / "outputs/secocha_pim_chain/source_acquisition/ingemmet_original_gis_manifest.json"
SERVICE = "https://geocatmin.ingemmet.gob.pe/arcgis/rest/services/SERV_PELIGROS_GEOLOGICOS/MapServer/6"
LAYER7_SERVICE = "https://geocatmin.ingemmet.gob.pe/arcgis/rest/services/SERV_PELIGROS_GEOLOGICOS/MapServer/7"
QUERY_WHERE = "CODIGO = 'A7367' AND DISTRITO = 'Mariano Nicolás Valcárcel' AND PROVINCIA = 'Camaná' AND FECHA_EVAL = 'febrero 2023'"
BUFFER_M = 5000.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    boundary = gpd.read_file(BOUNDARY, layer="secocha_active_boundary").to_crs(32718)
    if len(boundary) != 1:
        raise RuntimeError(f"expected one active Secocha boundary, got {len(boundary)}")
    bounds = boundary.geometry.buffer(BUFFER_M).to_crs(4326).total_bounds
    params = {
        "f": "geojson", "where": QUERY_WHERE, "outFields": "*", "returnGeometry": "true",
        "geometry": ",".join(f"{float(v):.8f}" for v in bounds),
        "geometryType": "esriGeometryEnvelope", "inSR": "4326", "outSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
    }
    url = SERVICE + "/query?" + urllib.parse.urlencode(params)
    context = ssl.create_default_context(cafile=certifi.where())
    request = urllib.request.Request(url, headers={"User-Agent": "IFPM-Secocha/1.0"})
    with urllib.request.urlopen(request, timeout=120, context=context) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("error"):
        raise RuntimeError(payload["error"])
    features = payload.get("features", [])
    if not features:
        raise RuntimeError("INGEMMET original hazard layer returned no features")
    expected = {"CODIGO": "A7367", "DISTRITO": "Mariano Nicolás Valcárcel",
                "PROVINCIA": "Camaná", "FECHA_EVAL": "febrero 2023"}
    for feature in features:
        attrs = feature.get("properties", {})
        mismatch = {field: attrs.get(field) for field, value in expected.items() if attrs.get(field) != value}
        if mismatch:
            raise RuntimeError(f"unexpected feature attributes in filtered result: {mismatch}")
    if len(features) != 3:
        raise RuntimeError(f"A7367 Secocha source contract expected 3 features, got {len(features)}")
    if payload.get("exceededTransferLimit"):
        raise RuntimeError("INGEMMET layer-6 query exceeded transfer limit; refusing a truncated source")
    metadata_url = SERVICE + "?f=json"
    metadata_request = urllib.request.Request(metadata_url, headers={"User-Agent": "IFPM-Secocha/1.0"})
    with urllib.request.urlopen(metadata_request, timeout=120, context=context) as response:
        metadata = json.loads(response.read().decode("utf-8"))
    if metadata.get("error"):
        raise RuntimeError(metadata["error"])
    # Preserve a negative check for the separate photointerpreted layer: it is
    # not the source of the three A7367 polygons used here.
    layer7_params = dict(params)
    layer7_url = LAYER7_SERVICE + "/query?" + urllib.parse.urlencode(layer7_params)
    layer7_error = None
    try:
        layer7_request = urllib.request.Request(layer7_url, headers={"User-Agent": "IFPM-Secocha/1.0"})
        with urllib.request.urlopen(layer7_request, timeout=120, context=context) as response:
            layer7_payload = json.loads(response.read().decode("utf-8"))
        if layer7_payload.get("error"):
            layer7_error = str(layer7_payload["error"])
            layer7_payload = {"features": []}
    except Exception as exc:  # diagnostic negative check must not block layer 6
        layer7_error = repr(exc)
        layer7_payload = {"features": []}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    partial = OUT_PATH.with_suffix(OUT_PATH.suffix + ".part")
    partial.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    partial.replace(OUT_PATH)
    gdf = gpd.read_file(OUT_PATH)
    manifest = {
        "dataset_id": "ingemmet_a7367_cartografia_peligros_secocha",
        "boundary_id": "secocha_reference_extent",
        "boundary_path": str(BOUNDARY.relative_to(ROOT)),
        "boundary_sha256": sha256(BOUNDARY),
        "access_date": str(date.today()), "source_service": SERVICE,
        "source_layer": "Cartografia de Peligros (MapServer layer 6)", "query_bounds_wgs84": list(map(float, bounds)),
        "query_buffer_m": BUFFER_M, "query_where": QUERY_WHERE, "query_url": url,
        "layer_metadata_url": metadata_url, "layer_id": 6,
        "service_metadata": {key: metadata.get(key) for key in ("name", "type", "maxRecordCount", "supportedQueryFormats", "supportsAdvancedQueries", "supportsStatistics")},
        "feature_count": int(len(gdf)), "geometry_type": sorted(gdf.geometry.geom_type.dropna().unique().tolist()),
        "source_crs": str(gdf.crs), "exceeded_transfer_limit": bool(payload.get("exceededTransferLimit", False)),
        "path": str(OUT_PATH.relative_to(ROOT)),
        "bytes": OUT_PATH.stat().st_size, "sha256": sha256(OUT_PATH),
        "attribute_filter_check": {
            "codigo_values": sorted(gdf["CODIGO"].dropna().astype(str).unique().tolist()),
            "danger_classes": sorted(gdf["PELIGRO_ES"].dropna().astype(str).unique().tolist()),
            "evaluation_dates": sorted(gdf["FECHA_EVAL"].dropna().astype(str).unique().tolist()),
        },
        "role": "original A7367 geological-hazard cartography; context evidence, not automatically the 2023-02-05 observed footprint",
        "claim_level": "validation_candidate",
        "negative_layer7_check": {
            "service": LAYER7_SERVICE, "layer_id": 7, "query_url": layer7_url,
            "feature_count": int(len(layer7_payload.get("features", []))),
            "query_error": layer7_error,
            "interpretation": (
                "No matching A7367 features in Cartografia Peligros Fotointerpretado layer 7."
                if layer7_error is None else "Layer-7 negative check could not be completed; see query_error."
            ),
        },
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"feature_count": len(gdf), "path": str(OUT_PATH.relative_to(ROOT)), "sha256": manifest["sha256"]}, indent=2))


if __name__ == "__main__":
    main()
