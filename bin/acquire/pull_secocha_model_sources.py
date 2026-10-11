#!/usr/bin/env python3
"""Acquire Secocha-specific sources required before the active PIM rerun.

Downloads the SRTMGL1 tile and queries official SERNANP and INGEMMET services
for the active Secocha reference extent plus documented context buffers.
WorldCover, WorldPop and Geofabrik Peru OSM are reused after the scope audit.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import ssl
import urllib.parse
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

import certifi
import geopandas as gpd
from shapely.geometry import Point, shape


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY = ROOT / "outputs/secocha_boundary/secocha_boundary.gpkg"
BOUNDARY_LAYER = "secocha_active_boundary"
BOUNDARY_ID = "secocha_reference_extent"
OUTPUT_ROOT_ID = "secocha_pim_chain"  # outputs folder name (differs from the id since 2026-10-11 rename)
OUT_DIR = ROOT / f"outputs/{OUTPUT_ROOT_ID}/source_acquisition"

SRTM_TILE = "S16W074"
SRTM_URL = f"https://step.esa.int/auxdata/dem/SRTMGL1/{SRTM_TILE}.SRTMGL1.hgt.zip"
SRTM_DIR = ROOT / "data/raw/srtm_1arcsec_secocha"
SRTM_TMP = ROOT / "data/tmp/srtm_1arcsec_secocha"
SRTM_PATH = SRTM_DIR / f"{SRTM_TILE}.SRTMGL1.hgt.zip"

INGEMMET_SERVICE = (
    "https://geocatminnube.ingemmet.gob.pe/arcgis/rest/services/"
    "SERV_PEQUENA_MINERIA/MapServer/0"
)
INGEMMET_DIR = ROOT / "data/raw/ingemmet_catastro_minero_secocha"
INGEMMET_GPKG = INGEMMET_DIR / "secocha_pequena_mineria.gpkg"

SERNANP_SERVICE = (
    "https://geoservicios.sernanp.gob.pe/arcgis/rest/services/"
    "servicios_ogc/peru_sernanp_0102/MapServer/0"
)
SERNANP_DIR = ROOT / "data/raw/sernanp_protected_areas_secocha"
SERNANP_GEOJSON = SERNANP_DIR / "secocha_sernanp_layer0_query.geojson"
SERNANP_BUFFER_M = 25_000.0
INGEMMET_BUFFER_M = 5_000.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def boundary_bounds(buffer_m: float) -> tuple[float, float, float, float]:
    boundary = gpd.read_file(BOUNDARY, layer=BOUNDARY_LAYER).to_crs("EPSG:32718")
    buffered = gpd.GeoDataFrame(geometry=boundary.geometry.buffer(buffer_m), crs=boundary.crs)
    return tuple(float(value) for value in buffered.to_crs("EPSG:4326").total_bounds)


def download_srtm() -> dict:
    SRTM_DIR.mkdir(parents=True, exist_ok=True)
    status = "already_present"
    if not SRTM_PATH.exists():
        SRTM_TMP.mkdir(parents=True, exist_ok=True)
        partial = SRTM_TMP / f"{SRTM_PATH.name}.part"
        request = urllib.request.Request(
            SRTM_URL,
            headers={"User-Agent": "IFPM-Secocha/1.0 research prototype"},
        )
        with urllib.request.urlopen(request, timeout=180) as response, partial.open("wb") as target:
            shutil.copyfileobj(response, target)
        if not zipfile.is_zipfile(partial):
            raise ValueError("SRTM download is not a ZIP archive")
        partial.replace(SRTM_PATH)
        status = "downloaded"
    with zipfile.ZipFile(SRTM_PATH) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".hgt")]
    if len(members) != 1 or SRTM_TILE not in Path(members[0]).name:
        raise ValueError(f"unexpected SRTM archive members: {members}")
    return {
        "dataset": "SRTMGL1 v3",
        "tile": SRTM_TILE,
        "status": status,
        "source_url": SRTM_URL,
        "path": rel(SRTM_PATH),
        "bytes": SRTM_PATH.stat().st_size,
        "sha256": sha256(SRTM_PATH),
        "hgt_member": members[0],
    }


def arcgis_query(service: str, bounds: tuple[float, float, float, float], *, geojson: bool) -> dict:
    params = {
        "f": "geojson" if geojson else "json",
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "geometry": ",".join(f"{value:.8f}" for value in bounds),
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "outSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "resultRecordCount": "1000",
    }
    url = service + "/query?" + urllib.parse.urlencode(params)
    context = ssl.create_default_context(cafile=certifi.where())
    request = urllib.request.Request(url, headers={"User-Agent": "IFPM-Secocha/1.0"})
    with urllib.request.urlopen(request, timeout=120, context=context) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("error"):
        raise RuntimeError(f"ArcGIS query failed: {payload['error']}")
    return {"url": url, "payload": payload}


def query_ingemmet() -> dict:
    bounds = boundary_bounds(INGEMMET_BUFFER_M)
    result = arcgis_query(INGEMMET_SERVICE, bounds, geojson=False)
    rows = []
    geometries = []
    for feature in result["payload"].get("features", []):
        geometry = feature.get("geometry") or {}
        if "x" in geometry and "y" in geometry:
            geometries.append(Point(float(geometry["x"]), float(geometry["y"])))
        elif "rings" in geometry:
            geometries.append(shape({"type": "Polygon", "coordinates": geometry["rings"]}))
        else:
            continue
        rows.append(feature.get("attributes") or {})
    gdf = gpd.GeoDataFrame(rows, geometry=geometries, crs="EPSG:4326")
    if gdf.empty:
        raise RuntimeError("INGEMMET returned no usable features for the Secocha context window")
    INGEMMET_DIR.mkdir(parents=True, exist_ok=True)
    if INGEMMET_GPKG.exists():
        INGEMMET_GPKG.unlink()
    gdf.to_file(INGEMMET_GPKG, layer="pequena_mineria", driver="GPKG")
    return {
        "dataset": "INGEMMET SERV_PEQUENA_MINERIA layer 0",
        "source": INGEMMET_SERVICE,
        "query_bounds_wgs84": list(bounds),
        "query_buffer_m": INGEMMET_BUFFER_M,
        "feature_count": len(gdf),
        "path": rel(INGEMMET_GPKG),
        "bytes": INGEMMET_GPKG.stat().st_size,
        "sha256": sha256(INGEMMET_GPKG),
        "role": "external mining overlay only; excluded from PIM score",
    }


def query_sernanp() -> dict:
    bounds = boundary_bounds(SERNANP_BUFFER_M)
    result = arcgis_query(SERNANP_SERVICE, bounds, geojson=True)
    payload = result["payload"]
    SERNANP_DIR.mkdir(parents=True, exist_ok=True)
    SERNANP_GEOJSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    feature_count = len(payload.get("features", []))
    return {
        "dataset": "SERNANP national definitive protected areas layer 0",
        "source": SERNANP_SERVICE,
        "query_bounds_wgs84": list(bounds),
        "query_buffer_m": SERNANP_BUFFER_M,
        "feature_count": feature_count,
        "path": rel(SERNANP_GEOJSON),
        "bytes": SERNANP_GEOJSON.stat().st_size,
        "sha256": sha256(SERNANP_GEOJSON),
        "interpretation": (
            "A zero feature count is confirmed absence in the queried national-definitive layer, "
            "not missing data. Regional/private/transitional layers remain outside this query."
        ),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "boundary_id": BOUNDARY_ID,
        "access_date": str(date.today()),
        "claim_level": "diagnostic_only",
        "sources": {
            "srtm": download_srtm(),
            "ingemmet_mining": query_ingemmet(),
            "sernanp": query_sernanp(),
        },
        "reused_sources": [
            "data/raw/esa_worldcover_2021_peru_former/ESA_WorldCover_10m_2021_v200_S18W075_Map.tif",
            "data/raw/worldpop_peru_population/per_ppp_2020_UNadj.tif",
            "data/raw/geofabrik_osm_peru_former/extracted/",
        ],
    }
    path = OUT_DIR / "source_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value.get("feature_count", value.get("status")) for key, value in manifest["sources"].items()}, indent=2))


if __name__ == "__main__":
    main()
