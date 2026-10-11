#!/usr/bin/env python3
"""Acquire official facility and mining layers that reduce Secocha proxies.

The outputs are external/context evidence only. They do not enter the PIM score.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import ssl
import subprocess
import urllib.parse
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import certifi
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY_PATH = ROOT / "outputs/secocha_boundary/secocha_boundary.gpkg"
BOUNDARY_LAYER = "secocha_active_boundary"
BOUNDARY_ID = "secocha_reference_extent"
METRIC_CRS = "EPSG:32718"

MINEDU_URL = (
    "https://escale.minedu.gob.pe/documents/inicio/Bases%20de%20datos/"
    "A.%20Censo%20Educativo/2023/00_Padron.zip"
)
MINEDU_DIR = ROOT / "data/raw/minedu_censo_educativo_2023_secocha"
MINEDU_ZIP = MINEDU_DIR / "00_Padron.zip"
MINEDU_DBF = MINEDU_DIR / "Padron.dbf"

MINAM_HEALTH_SERVICE = (
    "https://geoservidorperu.minam.gob.pe/arcgis/rest/services/"
    "hiroambienplanificacion/elementos_expuestos/MapServer/1"
)
MINAM_DIR = ROOT / "data/raw/minam_health_facilities_secocha"
MINAM_RAW = MINAM_DIR / "health_facilities_context.geojson"

INGEMMET_SERVICE = (
    "https://geocatmin.ingemmet.gob.pe/arcgis/rest/services/"
    "SERV_CATASTRO_MINERO_WGS84/MapServer"
)
INGEMMET_DIR = ROOT / "data/raw/ingemmet_catastro_minero_rights_secocha"
INGEMMET_RIGHTS_RAW = INGEMMET_DIR / "mining_rights_layer0_context.geojson"
INGEMMET_DGM_RAW = INGEMMET_DIR / "mining_activity_layer1_context.geojson"

OUTPUT_DIR = ROOT / "outputs/secocha_official_proxy_replacements"
OUTPUT_GPKG = OUTPUT_DIR / "secocha_official_exposure_mining.gpkg"
MANIFEST_PATH = OUTPUT_DIR / "proxy_replacement_manifest.json"
SUMMARY_PATH = OUTPUT_DIR / "proxy_replacement_summary.md"

FACILITY_CONTEXT_M = 25_000.0
MINING_CONTEXT_M = 5_000.0
MIN_REPORTABLE_OVERLAP_M2 = 1.0
USER_AGENT = "IFPM-Secocha/1.0 research prototype"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def artifact(path: Path) -> dict:
    return {"path": rel(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def download_atomic(url: str, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return "already_present"
    partial = destination.with_suffix(destination.suffix + ".part")
    partial.unlink(missing_ok=True)
    context = ssl.create_default_context(cafile=certifi.where())
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=180, context=context) as response, partial.open("wb") as target:
        shutil.copyfileobj(response, target)
    partial.replace(destination)
    return "downloaded"


def validate_arcgis_response(payload: dict, label: str) -> list[dict]:
    if payload.get("error"):
        raise RuntimeError(f"{label} service error: {payload['error']}")
    if payload.get("exceededTransferLimit"):
        raise RuntimeError(f"{label} transfer limit exceeded; refusing truncated data")
    features = payload.get("features")
    if not isinstance(features, list):
        raise RuntimeError(f"{label} response has no feature list")
    return features


def _request_json(url: str) -> dict:
    context = ssl.create_default_context(cafile=certifi.where())
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=120, context=context) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None)
        certificate_failure = isinstance(reason, ssl.SSLCertVerificationError) or (
            "CERTIFICATE_VERIFY_FAILED" in str(exc).upper()
            or "CERTIFICATE VERIFY FAILED" in str(exc).upper()
        )
        if not certificate_failure:
            raise
        completed = subprocess.run(
            [
                "curl",
                "-fsSL",
                "--max-time",
                "120",
                "--retry",
                "2",
                "--retry-all-errors",
                "-A",
                USER_AGENT,
                url,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return json.loads(completed.stdout.decode("utf-8"))


def query_arcgis_geojson(service: str, bounds: tuple[float, float, float, float], label: str) -> tuple[dict, dict]:
    common = {
        "where": "1=1",
        "geometry": ",".join(f"{value:.8f}" for value in bounds),
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
    }
    count_url = service + "/query?" + urllib.parse.urlencode(
        {**common, "returnCountOnly": "true", "f": "json"}
    )
    count_payload = _request_json(count_url)
    if count_payload.get("error"):
        raise RuntimeError(f"{label} count service error: {count_payload['error']}")
    expected_count = int(count_payload.get("count", -1))
    query_url = service + "/query?" + urllib.parse.urlencode(
        {
            **common,
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
        }
    )
    payload = _request_json(query_url)
    features = validate_arcgis_response(payload, label)
    if len(features) != expected_count:
        raise RuntimeError(
            f"{label} count mismatch: count query={expected_count}, GeoJSON={len(features)}"
        )
    return payload, {
        "service": service,
        "query_url": query_url,
        "count_url": count_url,
        "query_bounds_wgs84": list(bounds),
        "feature_count": len(features),
        "transfer_limit_check": "count matched returned features",
    }


def boundary_with_buffer(boundary: gpd.GeoDataFrame, distance_m: float) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"distance_m": [distance_m]},
        geometry=[boundary.geometry.union_all().buffer(distance_m)],
        crs=boundary.crs,
    )


def build_school_locations(
    services: pd.DataFrame,
    boundary: gpd.GeoDataFrame,
    *,
    context_buffer_m: float,
) -> tuple[gpd.GeoDataFrame, dict]:
    required = {
        "CODLOCAL",
        "COD_MOD",
        "ANEXO",
        "CEN_EDU",
        "NLAT_IE",
        "NLONG_IE",
        "IMPUTADO",
        "TALUMNO",
        "TDOCENTE",
    }
    missing = required - set(services.columns)
    if missing:
        raise RuntimeError(f"MINEDU Padron missing required fields: {sorted(missing)}")
    frame = services.copy()
    frame["NLAT_IE"] = pd.to_numeric(frame["NLAT_IE"], errors="coerce")
    frame["NLONG_IE"] = pd.to_numeric(frame["NLONG_IE"], errors="coerce")
    valid = (
        frame["NLAT_IE"].between(-90, 90)
        & frame["NLONG_IE"].between(-180, 180)
        & ~((frame["NLAT_IE"] == 0) & (frame["NLONG_IE"] == 0))
    )
    invalid_count = int((~valid).sum())
    frame = frame.loc[valid].copy()
    points = gpd.GeoDataFrame(
        frame,
        geometry=gpd.points_from_xy(frame["NLONG_IE"], frame["NLAT_IE"]),
        crs="EPSG:4326",
    ).to_crs(boundary.crs)
    context = boundary.geometry.union_all().buffer(context_buffer_m)
    points = points.loc[points.geometry.intersects(context)].copy()
    if points.empty:
        raise RuntimeError("MINEDU Padron has no valid school locations in the context window")

    points["TALUMNO"] = pd.to_numeric(points["TALUMNO"], errors="coerce").fillna(0)
    points["TDOCENTE"] = pd.to_numeric(points["TDOCENTE"], errors="coerce").fillna(0)
    codlocal = points["CODLOCAL"].astype("string").str.strip()
    missing_codlocal = codlocal.isna() | codlocal.eq("") | codlocal.str.lower().eq("nan")
    points["location_id"] = codlocal
    points.loc[missing_codlocal, "location_id"] = (
        "SERVICE:"
        + points.loc[missing_codlocal, "COD_MOD"].astype(str).str.strip()
        + ":"
        + points.loc[missing_codlocal, "ANEXO"].astype(str).str.strip()
    )
    missing_codlocal_count = int(missing_codlocal.sum())
    records = []
    for location_id, group in points.groupby("location_id", sort=True):
        record_provenance = resolve_record_provenance(group["IMPUTADO"])
        geom = Point(float(group.geometry.x.median()), float(group.geometry.y.median()))
        coordinate_spread_m = float(group.geometry.distance(geom).max())
        names = sorted({str(value).strip() for value in group["CEN_EDU"].dropna() if str(value).strip()})
        source_codlocal = group["CODLOCAL"].dropna().astype(str).str.strip()
        record = {
            "location_id": str(location_id),
            "source_codlocal": source_codlocal.iloc[0] if len(source_codlocal) else None,
            "location_id_status": (
                "codlocal"
                if not str(location_id).startswith("SERVICE:")
                else "missing_codlocal_service_level"
            ),
            "service_count": int(group["COD_MOD"].astype(str).nunique()),
            "education_names": " | ".join(names),
            "reported_student_service_sum": int(group["TALUMNO"].sum()),
            "reported_teacher_service_sum": int(group["TDOCENTE"].sum()),
            "record_provenance": record_provenance,
            "coordinate_spread_m": round(coordinate_spread_m, 1),
            "position_limit": "statistical reference location; not building-accurate",
            "count_limit": "student/teacher values are sums across service records, not deduplicated persons",
            "source_year": 2023,
            "geometry": geom,
        }
        records.append(record)
    locations = gpd.GeoDataFrame(records, geometry="geometry", crs=boundary.crs)
    active = boundary.geometry.union_all()
    locations["inside_active_boundary"] = locations.geometry.intersects(active)
    locations["distance_to_boundary_m"] = locations.geometry.distance(active).round(1)
    quality = {
        "service_records_total": int(len(services)),
        "invalid_coordinate_records": invalid_count,
        "missing_codlocal_service_records": missing_codlocal_count,
        "valid_service_records_in_context": int(len(points)),
        "unique_locations": int(len(locations)),
        "inside_active_boundary": int(locations["inside_active_boundary"].sum()),
        "record_provenance_counts": {
            str(key): int(value)
            for key, value in locations["record_provenance"].value_counts().sort_index().items()
        },
        "max_coordinate_spread_m": float(locations["coordinate_spread_m"].max()),
    }
    return locations, quality


def write_geojson_atomic(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    partial.replace(path)


def write_text_atomic(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_text(text, encoding="utf-8")
    partial.replace(path)


def resolve_record_provenance(values) -> str:
    provenance_map = {"1": "declared", "2": "imputed_total", "3": "imputed_partial"}
    resolved = {provenance_map.get(str(value), "unknown") for value in values}
    if len(resolved) == 1:
        return next(iter(resolved))
    if {"imputed_total", "imputed_partial"} & resolved:
        return "mixed_with_imputation"
    return "mixed_or_unknown"


def sanitize_health(
    raw: gpd.GeoDataFrame,
    boundary: gpd.GeoDataFrame,
    *,
    max_context_m: float,
) -> gpd.GeoDataFrame:
    keep = [
        "OBJECTID",
        "departamen",
        "provincia",
        "distrito",
        "localidad",
        "codigo_min",
        "nombre_del",
        "direccion",
        "categoria",
        "fuente",
        "fuente_des",
        "geometry",
    ]
    clean = raw[[column for column in keep if column in raw.columns]].to_crs(boundary.crs).copy()
    active = boundary.geometry.union_all()
    clean["distance_to_boundary_m"] = clean.geometry.distance(active)
    clean = clean.loc[clean["distance_to_boundary_m"] <= max_context_m + 0.01].copy()
    clean["inside_active_boundary"] = clean.geometry.intersects(active)
    clean["distance_to_boundary_m"] = clean["distance_to_boundary_m"].round(1)
    clean["position_limit"] = "source warns point may represent populated-centre location, not exact building"
    return clean


def sanitize_mining(
    raw: gpd.GeoDataFrame,
    boundary: gpd.GeoDataFrame,
    source_layer: int,
    *,
    max_context_m: float,
) -> gpd.GeoDataFrame:
    denouncement_date = pd.to_datetime(
        pd.to_numeric(raw.get("FEC_DENU"), errors="coerce"), unit="ms", utc=True, errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    source_update_date = pd.to_datetime(
        pd.to_numeric(raw.get("FECHA_ACTUALIZACION"), errors="coerce"),
        unit="ms",
        utc=True,
        errors="coerce",
    ).dt.strftime("%Y-%m-%d")
    keep = [
        "OBJECTID",
        "CODIGOU",
        "CONCESION",
        "HECTAGIS",
        "ESTADO",
        "D_ESTADO",
        "LEYENDA",
        "ESTADO_MINEM",
        "SUSTANCIA",
        "DEPA",
        "PROVI",
        "DISTRI",
        "geometry",
    ]
    clean = raw[[column for column in keep if column in raw.columns]].to_crs(boundary.crs).copy()
    clean["denouncement_date"] = denouncement_date
    clean["source_update_date"] = source_update_date
    active = boundary.geometry.union_all()
    clean["distance_to_boundary_m"] = clean.geometry.distance(active)
    clean = clean.loc[clean["distance_to_boundary_m"] <= max_context_m + 0.01].copy()
    clean["distance_to_boundary_m"] = clean["distance_to_boundary_m"].round(1)
    clean["source_layer"] = source_layer
    clean["intersects_active_boundary"] = clean.geometry.intersects(active)
    clean["touches_active_boundary"] = clean.geometry.touches(active)
    intersections = clean.geometry.intersection(active)
    clean["active_overlap_ha"] = (intersections.area / 10_000.0).round(3)
    clean["positive_area_overlap"] = intersections.area >= MIN_REPORTABLE_OVERLAP_M2
    clean["evidence_limit"] = "legal/cadastral right; not verified active extraction footprint"
    return clean


def main() -> None:
    started = datetime.now(timezone.utc)
    boundary = gpd.read_file(BOUNDARY_PATH, layer=BOUNDARY_LAYER).to_crs(METRIC_CRS)
    if len(boundary) != 1:
        raise RuntimeError(f"expected one active Secocha boundary, got {len(boundary)}")

    minedu_status = download_atomic(MINEDU_URL, MINEDU_ZIP)
    if not zipfile.is_zipfile(MINEDU_ZIP):
        raise RuntimeError("MINEDU 2023 Padron download is not a ZIP archive")
    with zipfile.ZipFile(MINEDU_ZIP) as archive:
        members = [member for member in archive.namelist() if Path(member).name == "Padron.dbf"]
        if len(members) != 1:
            raise RuntimeError(f"expected one Padron.dbf in MINEDU archive, got {members}")
        MINEDU_DIR.mkdir(parents=True, exist_ok=True)
        dbf_partial = MINEDU_DBF.with_suffix(".dbf.part")
        dbf_partial.unlink(missing_ok=True)
        with archive.open(members[0]) as source, dbf_partial.open("wb") as target:
            shutil.copyfileobj(source, target)
        dbf_partial.replace(MINEDU_DBF)
    school_services = gpd.read_file(MINEDU_DBF)
    schools, school_quality = build_school_locations(
        school_services, boundary, context_buffer_m=FACILITY_CONTEXT_M
    )

    facility_bounds = tuple(
        boundary_with_buffer(boundary, FACILITY_CONTEXT_M).to_crs(4326).total_bounds
    )
    health_payload, health_query = query_arcgis_geojson(
        MINAM_HEALTH_SERVICE, facility_bounds, "MINAM health facilities"
    )
    write_geojson_atomic(health_payload, MINAM_RAW)
    health = sanitize_health(
        gpd.read_file(MINAM_RAW), boundary, max_context_m=FACILITY_CONTEXT_M
    )

    mining_bounds = tuple(
        boundary_with_buffer(boundary, MINING_CONTEXT_M).to_crs(4326).total_bounds
    )
    rights_payload, rights_query = query_arcgis_geojson(
        f"{INGEMMET_SERVICE}/0", mining_bounds, "INGEMMET mining rights layer 0"
    )
    dgm_payload, dgm_query = query_arcgis_geojson(
        f"{INGEMMET_SERVICE}/1", mining_bounds, "INGEMMET DGM activity layer 1"
    )
    write_geojson_atomic(rights_payload, INGEMMET_RIGHTS_RAW)
    write_geojson_atomic(dgm_payload, INGEMMET_DGM_RAW)
    rights = sanitize_mining(
        gpd.read_file(INGEMMET_RIGHTS_RAW),
        boundary,
        0,
        max_context_m=MINING_CONTEXT_M,
    )
    dgm = (
        sanitize_mining(
            gpd.read_file(INGEMMET_DGM_RAW),
            boundary,
            1,
            max_context_m=MINING_CONTEXT_M,
        )
        if dgm_query["feature_count"]
        else rights.iloc[0:0].copy()
    )
    dgm["source_layer"] = pd.Series(dtype="int64") if dgm.empty else dgm["source_layer"]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    gpkg_partial = OUTPUT_GPKG.with_name(OUTPUT_GPKG.stem + ".part.gpkg")
    gpkg_partial.unlink(missing_ok=True)
    schools.to_file(gpkg_partial, layer="minedu_education_locations_2023", driver="GPKG")
    health.to_file(gpkg_partial, layer="minam_health_facilities_context", driver="GPKG")
    rights.to_file(gpkg_partial, layer="ingemmet_mining_rights", driver="GPKG")
    dgm.to_file(
        gpkg_partial,
        layer="ingemmet_dgm_activity",
        driver="GPKG",
        geometry_type="Polygon",
    )
    gpkg_partial.replace(OUTPUT_GPKG)

    finished = datetime.now(timezone.utc)
    manifest = {
        "dataset_id": "secocha_official_proxy_replacements",
        "boundary_id": BOUNDARY_ID,
        "boundary": artifact(BOUNDARY_PATH),
        "boundary_layer": BOUNDARY_LAYER,
        "boundary_crs": METRIC_CRS,
        "facility_context_filter_m": FACILITY_CONTEXT_M,
        "mining_context_filter_m": MINING_CONTEXT_M,
        "minimum_reportable_overlap_m2": MIN_REPORTABLE_OVERLAP_M2,
        "run_started_utc": started.isoformat(),
        "run_finished_utc": finished.isoformat(),
        "claim_level": "context_evidence",
        "enters_pim_score": False,
        "sources": {
            "minedu_education_2023": {
                "source": "MINEDU ESCALE Censo Educativo 2023 Padron",
                "source_url": MINEDU_URL,
                "download_status": minedu_status,
                "raw_archive": artifact(MINEDU_ZIP),
                "raw_dbf": artifact(MINEDU_DBF),
                "quality": school_quality,
                "grain": "CODLOCAL location; missing CODLOCAL is retained at service-record level",
                "source_vintage": "Censo Educativo 2023; event-date operating status not established",
                "position_limit": "official statistical reference location; not building-accurate",
                "count_limit": "student/teacher fields are reported service-row sums, not deduplicated persons",
                "privacy": "raw DBF contains director/contact fields; processed layer excludes them",
            },
            "minam_health_facilities": {
                **health_query,
                "raw": artifact(MINAM_RAW),
                "processed_count": int(len(health)),
                "exact_context_filter_m": FACILITY_CONTEXT_M,
                "inside_active_boundary": int(health["inside_active_boundary"].sum()),
                "position_limit": "official service warns locations may represent populated centres rather than exact buildings",
                "source_as_of": "live service queried at run_finished_utc; 2023 event-date status not established",
            },
            "ingemmet_mining_rights": {
                **rights_query,
                "raw": artifact(INGEMMET_RIGHTS_RAW),
                "processed_count": int(len(rights)),
                "exact_context_filter_m": MINING_CONTEXT_M,
                "max_distance_to_boundary_m": float(rights["distance_to_boundary_m"].max()),
                "intersects_active_boundary": int(rights["intersects_active_boundary"].sum()),
                "touches_active_boundary": int(rights["touches_active_boundary"].sum()),
                "positive_area_overlap": int(rights["positive_area_overlap"].sum()),
                "positive_area_definition": f"intersection area >= {MIN_REPORTABLE_OVERLAP_M2:g} m2",
                "status_counts": {
                    str(key): int(value)
                    for key, value in rights["LEYENDA"].value_counts().sort_index().items()
                },
                "semantic_limit": "referential legal/cadastral rights; not active extraction footprint",
            },
            "ingemmet_dgm_activity": {
                **dgm_query,
                "raw": artifact(INGEMMET_DGM_RAW),
                "processed_count": int(len(dgm)),
                "exact_context_filter_m": MINING_CONTEXT_M,
                "intersects_active_boundary": int(dgm["intersects_active_boundary"].sum()),
                "positive_area_overlap": int(dgm["positive_area_overlap"].sum()),
                "semantic_limit": "DGM administrative concession status, not field-verified active extraction; zero records is not proof of no informal activity",
            },
        },
        "processed": {
            **artifact(OUTPUT_GPKG),
            "layers": [
                "minedu_education_locations_2023",
                "minam_health_facilities_context",
                "ingemmet_mining_rights",
                "ingemmet_dgm_activity",
            ]
        },
        "interpretation": (
            "These layers reduce reliance on WorldCover built-up and mining-point proxies, "
            "but remain external evidence until an explicit PIM design decision is approved."
        ),
    }
    write_text_atomic(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", MANIFEST_PATH)
    write_text_atomic(
        "# Secocha official proxy replacements\n\n"
        f"- MINEDU 2023 educational locations within 25 km: {len(schools)} "
        f"({school_quality['inside_active_boundary']} inside active frame).\n"
        f"- MINAM health facilities within 25 km: {len(health)} "
        f"({int(health['inside_active_boundary'].sum())} inside active frame).\n"
        f"- INGEMMET mining-right polygons after exact 5 km filtering: {len(rights)}; "
        f"{int(rights['positive_area_overlap'].sum())} have positive-area overlap and "
        f"{int(rights['touches_active_boundary'].sum())} only touch the frame boundary.\n"
        f"- INGEMMET DGM administrative EXPLOTACION-status records after exact 5 km filtering: {len(dgm)}.\n\n"
        "All layers are context outside the PIM score; mining rights are concessions, not extraction footprints.\n",
        SUMMARY_PATH,
    )
    print(json.dumps({
        "schools": len(schools),
        "health": len(health),
        "mining_rights": len(rights),
        "dgm_activity": len(dgm),
        "output": rel(OUTPUT_GPKG),
    }, indent=2))


if __name__ == "__main__":
    main()
