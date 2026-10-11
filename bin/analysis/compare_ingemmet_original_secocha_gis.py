#!/usr/bin/env python3
"""Compare the original INGEMMET A7367 GIS polygons with the PDF candidate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT / "data/raw/ingemmet_a7367_cartografia_peligros_secocha/ingemmet_a7367_cartografia_peligros_layer6_secocha.geojson"
EVENT_GPKG = ROOT / "outputs/secocha_2023_validation/observed_hazard/secocha_2023_map7_event_digitization.gpkg"
BOUNDARY = ROOT / "outputs/secocha_boundary/secocha_boundary.gpkg"
OUT = ROOT / "outputs/secocha_2023_validation/observed_hazard"
REPORT = OUT / "ingemmet_original_gis_comparison.json"
FIGURE = OUT / "ingemmet_original_vs_pdf_candidate.png"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    original = gpd.read_file(ORIGINAL).to_crs(32718)
    event = gpd.read_file(EVENT_GPKG, layer="event_footprint_candidate").geometry.iloc[0]
    boundary_gdf = gpd.read_file(BOUNDARY, layer="secocha_active_boundary")
    if len(boundary_gdf) != 1:
        raise RuntimeError(f"expected one active boundary feature, got {len(boundary_gdf)}")
    boundary = boundary_gdf.geometry.iloc[0]
    required = {"OBJECTID", "PELIGRO_ES", "CODIGO", "TITULO", "FECHA_EVAL", "DOCUMENTO", "EAM", "GPELIGRO"}
    if not required.issubset(original.columns):
        raise RuntimeError(f"original GIS schema missing {sorted(required - set(original.columns))}")
    if len(original) != 3 or not original.geometry.is_valid.all() or (original.geometry.area <= 0).any():
        raise RuntimeError("original A7367 GIS failed feature-count, geometry-validity, or positive-area checks")
    if event.is_empty or not event.is_valid or event.area <= 0:
        raise RuntimeError("PDF event candidate is empty or invalid")
    source_manifest_path = ROOT / "outputs/secocha_pim_chain/source_acquisition/ingemmet_original_gis_manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    if source_manifest["sha256"] != sha256(ORIGINAL):
        raise RuntimeError("original GIS checksum differs from acquisition manifest")
    if source_manifest["boundary_sha256"] != sha256(BOUNDARY):
        raise RuntimeError("active boundary checksum differs from original GIS acquisition manifest")
    union = original.geometry.union_all()

    rows = []
    for _, row in original.iterrows():
        geometry = row.geometry
        rows.append({
            "objectid": int(row.OBJECTID), "hazard_class": row.PELIGRO_ES,
            "activity": row.EAM, "geological_hazard_level": row.GPELIGRO,
            "area_km2": float(geometry.area / 1e6),
            "active_boundary_overlap_km2": float(geometry.intersection(boundary).area / 1e6),
            "pdf_event_candidate_overlap_km2": float(geometry.intersection(event).area / 1e6),
            "source_code": row.CODIGO, "source_title": row.TITULO,
            "evaluation_date": row.FECHA_EVAL, "document": row.DOCUMENTO,
        })

    flow_features = original[original["PELIGRO_ES"].astype(str) == "Flujo de detritos"]
    if len(flow_features) != 1 or flow_features.geometry.iloc[0].is_empty or flow_features.geometry.iloc[0].area <= 0:
        raise RuntimeError("original A7367 GIS does not contain exactly one valid Flujo de detritos polygon")
    flow = flow_features.geometry.union_all()
    report = {
        "source": "INGEMMET SERV_PELIGROS_GEOLOGICOS MapServer layer 6",
        "source_url": "https://geocatmin.ingemmet.gob.pe/arcgis/rest/services/SERV_PELIGROS_GEOLOGICOS/MapServer/6",
        "query_role": "original A7367 cartography polygons, not analyst digitization",
        "source_file": str(ORIGINAL.relative_to(ROOT)), "source_sha256": sha256(ORIGINAL),
        "source_manifest": str(source_manifest_path.relative_to(ROOT)),
        "query_where": source_manifest["query_where"],
        "feature_count": int(len(original)), "crs": "EPSG:32718 after reprojection",
        "attribute_filter": {"CODIGO": "A7367", "DISTRITO": "Mariano Nicolás Valcárcel",
                             "PROVINCIA": "Camaná", "FECHA_EVAL": "febrero 2023"},
        "total_area_km2": float(union.area / 1e6),
        "active_boundary_overlap_km2": float(union.intersection(boundary).area / 1e6),
        "pdf_event_candidate_area_km2": float(event.area / 1e6),
        "pdf_event_candidate_covered_by_original_fraction": float(event.intersection(union).area / event.area),
        "pdf_event_candidate_covered_by_flow_only_fraction": float(event.intersection(flow).area / event.area),
        "features": rows,
        "interpretation": "The original polygons are A7367 general geological-hazard cartography. They corroborate the PDF candidate spatially but are not automatically the 2023-02-05 observed footprint.",
        "claim_level": "validation_candidate",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    fig, ax = plt.subplots(figsize=(9, 8), facecolor="white")
    original.plot(ax=ax, column="PELIGRO_ES", categorical=True, alpha=.38,
                  edgecolor="#333333", linewidth=.6, legend=True)
    gpd.GeoSeries([boundary], crs=32718).boundary.plot(ax=ax, color="#111111", linewidth=1.1,
                                                        linestyle="--", label="Active Secocha boundary")
    gpd.GeoSeries([event], crs=32718).boundary.plot(ax=ax, color="#00a6d6", linewidth=1.4,
                                                     label="PDF 5 February candidate")
    ax.set_title("Original INGEMMET A7367 polygons vs. PDF event candidate", fontweight="bold")
    ax.set_xlabel("UTM 18S easting (m)"); ax.set_ylabel("UTM 18S northing (m)")
    ax.legend(loc="lower left", fontsize=8)
    fig.text(.06, .02,
             "Original polygons are general A7367 geological-hazard cartography; the cyan outline is the semi-automatic 5 February candidate.",
             fontsize=8.5, color="#444444")
    fig.tight_layout(rect=(0, .05, 1, 1))
    fig.savefig(FIGURE, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
