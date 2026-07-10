#!/usr/bin/env python3
"""Download Peru/Arequipa flood-relevant SINPAD emergency records.

This script queries the public INDECI SINPAD ArcGIS REST service, filters
flood/rainfall/aluvion-related events in Arequipa, and writes raw validation
points under data/validation. It also creates a PE1-study-area context subset
and simple summary tables under outputs.
"""

from __future__ import annotations

import csv
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import geopandas as gpd
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[2]
SERVICE = (
    "https://geosinpad.indeci.gob.pe/indeci/rest/services/"
    "Emergencias/EMERGENCIAS_SINPAD/MapServer/0"
)
PE1_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
RAW_DIR = ROOT / "data/validation/indeci_sinpad_peru_flood_events"
OUT_DIR = ROOT / "outputs/indeci_sinpad_peru_flood_events"

FIELDS = [
    "IDE_SINPAD",
    "FECHA",
    "ANHO",
    "MES",
    "COD_UBIGEO",
    "DEPARTAMENTO",
    "PROVINCIA",
    "DISTRITO",
    "FENOMENO",
    "DES_GRUPAL_FENOMENO",
    "SAFECTA",
    "SDAMNI",
    "SFALLE",
    "SLESI",
    "SDESTRUVIVI",
    "SINHABIVIVI",
    "SAFECTAVIVI",
    "SDESTRU_SALUD",
    "SAFECTA_SALUD",
    "SINHABI_SALUD",
    "SCAMIRURAL_AFECTA",
    "SCAMIRURAL_DESTRU",
    "SCARRE_AFECTA",
    "SCARRE_DESTRU",
    "SPUENTE_AFECTA",
    "SPUENTE_DESTRU",
    "SAGUAPOTA_AFECTA",
    "SAGUAPOTA_DESTRU",
    "SENERGIA_AFECTA",
    "SENERGIA_DESTRU",
    "SAREACULTI_AFECTA",
    "SAREACULTI_PERDIDO",
    "NUM_POSX",
    "NUM_POSY",
]

INPUTS = [ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"]
OUTPUTS = [
    ROOT / "data/validation/indeci_sinpad_peru_flood_events/arequipa_sinpad_flood_relevant.gpkg",
    ROOT / "data/validation/indeci_sinpad_peru_flood_events/arequipa_sinpad_flood_relevant.csv",
    ROOT / "data/validation/indeci_sinpad_peru_flood_events/pe1_sinpad_flood_relevant.gpkg",
    ROOT / "data/validation/indeci_sinpad_peru_flood_events/pe1_sinpad_flood_relevant.csv",
    ROOT / "data/validation/indeci_sinpad_peru_flood_events/pe1_plus20km_sinpad_flood_relevant.gpkg",
    ROOT / "outputs/indeci_sinpad_peru_flood_events/arequipa_sinpad_fenomeno_summary.csv",
    ROOT / "outputs/indeci_sinpad_peru_flood_events/pe1_sinpad_fenomeno_summary.csv",
    ROOT / "outputs/indeci_sinpad_peru_flood_events/pe1_plus20km_sinpad_fenomeno_summary.csv",
    ROOT / "outputs/indeci_sinpad_peru_flood_events/sinpad_download_manifest.json",
]

# Keep this broad for validation discovery. It intentionally includes intense
# rainfall and debris-flow style hazards because the mentor's validation ask is
# flood-prioritisation in semi-arid mining catchments, not only river overflow.
FLOOD_RELEVANT_SQL = " OR ".join(
    [
        "FENOMENO LIKE '%INUND%'",
        "FENOMENO LIKE '%LLUVI%'",
        "FENOMENO LIKE '%ALUVI%'",
        "FENOMENO LIKE '%HUAY%'",
        "FENOMENO LIKE '%DESBORDE%'",
    ]
)
WHERE = f"DEPARTAMENTO='AREQUIPA' AND ({FLOOD_RELEVANT_SQL})"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def query_sinpad() -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    offset = 0
    page = 2000
    while True:
        params = {
            "f": "json",
            "where": WHERE,
            "outFields": ",".join(FIELDS),
            "returnGeometry": "true",
            "outSR": "4326",
            "resultOffset": str(offset),
            "resultRecordCount": str(page),
            "orderByFields": "ANHO DESC, IDE_SINPAD DESC",
        }
        url = SERVICE + "/query?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("error"):
            raise RuntimeError(f"SINPAD ArcGIS error: {data['error']}")
        batch = data.get("features", [])
        features.extend(batch)
        if len(batch) < page or data.get("exceededTransferLimit") is not True:
            break
        offset += page
    return features


def features_to_gdf(features: list[dict[str, Any]]) -> gpd.GeoDataFrame:
    rows: list[dict[str, Any]] = []
    geoms: list[Point] = []
    for feature in features:
        attrs = feature.get("attributes", {}).copy()
        geom = feature.get("geometry", {})
        x = geom.get("x", attrs.get("NUM_POSX"))
        y = geom.get("y", attrs.get("NUM_POSY"))
        try:
            x_val = float(x)
            y_val = float(y)
        except (TypeError, ValueError):
            continue
        if not (-82 <= x_val <= -68 and -19 <= y_val <= 1):
            continue
        geoms.append(Point(x_val, y_val))
        rows.append(attrs)
    return gpd.GeoDataFrame(rows, geometry=geoms, crs="EPSG:4326")


def summarize(gdf: gpd.GeoDataFrame, out_csv: Path) -> None:
    numeric_cols = [
        "SAFECTA",
        "SDAMNI",
        "SFALLE",
        "SLESI",
        "SCARRE_AFECTA",
        "SCARRE_DESTRU",
        "SPUENTE_AFECTA",
        "SPUENTE_DESTRU",
        "SDESTRUVIVI",
        "SINHABIVIVI",
        "SAFECTAVIVI",
    ]
    rows = []
    if not gdf.empty:
        for phenomenon, sub in gdf.groupby("FENOMENO", dropna=False):
            row: dict[str, Any] = {"fenomeno": phenomenon, "event_count": len(sub)}
            for col in numeric_cols:
                if col in sub:
                    row[f"{col.lower()}_sum"] = float(sub[col].fillna(0).sum())
            rows.append(row)
    fieldnames = sorted({key for row in rows for key in row.keys()}) or ["fenomeno", "event_count"]
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_manifest(raw_gpkg: Path, pe1_gpkg: Path, raw_count: int, pe1_count: int) -> None:
    manifest = {
        "dataset_id": "indeci_sinpad_peru_flood_events",
        "source": SERVICE,
        "where": WHERE,
        "raw_gpkg": rel(raw_gpkg),
        "raw_sha256": sha256_file(raw_gpkg),
        "raw_size_bytes": raw_gpkg.stat().st_size,
        "arequipa_flood_relevant_records_with_valid_geometry": raw_count,
        "pe1_boundary_records": pe1_count,
        "claim_level": "diagnostic_only",
        "evidence_role": "event_point_colocation_context",
        "note": (
            "Official SINPAD emergency records for flood/rainfall/aluvion-style "
            "hazards. Use for validation/enrichment checks, not as proof of final "
            "flood-risk validity."
        ),
    }
    manifest_path = OUT_DIR / "sinpad_download_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Querying INDECI SINPAD Arequipa flood-relevant records...")
    features = query_sinpad()
    gdf = features_to_gdf(features)
    print(f"records returned: {len(features)}; valid geometries: {len(gdf)}")

    raw_gpkg = RAW_DIR / "arequipa_sinpad_flood_relevant.gpkg"
    raw_csv = RAW_DIR / "arequipa_sinpad_flood_relevant.csv"
    gdf.to_file(raw_gpkg, layer="sinpad_arequipa_flood_relevant", driver="GPKG")
    gdf.drop(columns="geometry").to_csv(raw_csv, index=False)
    print(f"wrote: {rel(raw_gpkg)}")
    print(f"wrote: {rel(raw_csv)}")

    boundary = gpd.read_file(PE1_GPKG, layer="peru_pilot_boundary").to_crs(gdf.crs)
    # Write exact study-boundary events. If the count is low, downstream
    # validation can also use a buffered context, but this exact subset stays
    # unambiguous.
    pe1 = gpd.sjoin(gdf, boundary[["geometry"]], predicate="within", how="inner")
    pe1 = pe1.drop(columns=[c for c in ["index_right"] if c in pe1.columns])
    pe1_gpkg = RAW_DIR / "pe1_sinpad_flood_relevant.gpkg"
    pe1_csv = RAW_DIR / "pe1_sinpad_flood_relevant.csv"
    pe1.to_file(pe1_gpkg, layer="sinpad_pe1_flood_relevant", driver="GPKG")
    pe1.drop(columns="geometry").to_csv(pe1_csv, index=False)
    print(f"PE1 boundary records: {len(pe1)}")

    buffer_m = 20_000
    boundary_m = boundary.to_crs("EPSG:32718")
    buffered = boundary_m.copy()
    buffered["geometry"] = boundary_m.geometry.buffer(buffer_m)
    buffered = buffered.to_crs(gdf.crs)
    pe1_buffer = gpd.sjoin(gdf, buffered[["geometry"]], predicate="within", how="inner")
    pe1_buffer = pe1_buffer.drop(columns=[c for c in ["index_right"] if c in pe1_buffer.columns])
    pe1_buffer_gpkg = RAW_DIR / "pe1_plus20km_sinpad_flood_relevant.gpkg"
    pe1_buffer.to_file(pe1_buffer_gpkg, layer="sinpad_pe1_plus20km_flood_relevant", driver="GPKG")
    print(f"PE1 + 20 km records: {len(pe1_buffer)}")

    summarize(gdf, OUT_DIR / "arequipa_sinpad_fenomeno_summary.csv")
    summarize(pe1, OUT_DIR / "pe1_sinpad_fenomeno_summary.csv")
    summarize(pe1_buffer, OUT_DIR / "pe1_plus20km_sinpad_fenomeno_summary.csv")
    write_manifest(raw_gpkg, pe1_gpkg, len(gdf), len(pe1))
    print(f"wrote summary/manifest under: {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
