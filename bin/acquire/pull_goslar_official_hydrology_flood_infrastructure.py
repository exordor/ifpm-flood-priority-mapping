#!/usr/bin/env python3
"""Acquire official Goslar hydrology/flood context and OSM infrastructure.

The script stores source archives under ``data/raw`` and derived focus-context
layers under ``outputs/goslar_official_hydrology_and_flood_data``.  It is
intentionally resumable: already-present archives are checksummed and reused.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import date
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/goslar_official_hydrology_and_flood_data"
VALIDATION = ROOT / "data/validation/goslar_harz_2024_focus_area/official_event_and_hazard_data"
OUT = ROOT / "outputs/goslar_official_hydrology_and_flood_data"

SOURCES = {
    "basins": {
        "url": "https://www.umweltkarten-niedersachsen.de/Download_OE/WRRL/DrainBasin_Waterbody_LOCAL.zip",
        "filename": "DrainBasin_Waterbody_LOCAL.zip",
    },
    "river_segments": {
        "url": "https://www.umweltkarten-niedersachsen.de/Download_OE/WRRL/WFD_RWSEG_LOCAL.zip",
        "filename": "WFD_RWSEG_LOCAL.zip",
    },
    "oker_hazard": {
        "url": "https://www.umweltkarten-niedersachsen.de/Download_OE/HWRM-RL/Daten/HWRM-RL_Daten_Oker.zip",
        "filename": "HWRM-RL_Daten_Oker.zip",
    },
    "innerste_hazard": {
        "url": "https://www.umweltkarten-niedersachsen.de/Download_OE/HWRM-RL/Daten/HWRM-RL_Daten_Innerste.zip",
        "filename": "HWRM-RL_Daten_Innerste.zip",
    },
    "nlwkn_2017_report": {
        "url": "https://www.nlwkn.niedersachsen.de/download/124949/Hochwasserbericht_Juli_2017.pdf",
        "filename": "NLWKN_Hochwasserbericht_Juli_2017.pdf",
        "validation": True,
    },
}

INFRA_QUERY = """[out:json][timeout:120];
area["boundary"="administrative"]["name"="Landkreis Goslar"]->.a;
(
  nwr["amenity"="school"](area.a);
  nwr["amenity"="hospital"](area.a);
  nwr["amenity"="fire_station"](area.a);
  nwr["amenity"="police"](area.a);
  nwr["emergency"](area.a);
  nwr["healthcare"](area.a);
  nwr["man_made"="works"](area.a);
  nwr["power"="substation"](area.a);
  nwr["railway"="station"](area.a);
);
out center;
"""
INFRA_CLASSES = {
    "school",
    "hospital",
    "fire_station",
    "police",
    "works",
    "substation",
    "station",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, path: Path) -> None:
    import urllib.request

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    tmp = path.with_suffix(path.suffix + ".part")
    with urllib.request.urlopen(url, timeout=300) as response, tmp.open("wb") as out:
        shutil.copyfileobj(response, out)
    tmp.replace(path)


def extract_shapefile(archive: Path, stem: str, destination: Path) -> Path:
    with zipfile.ZipFile(archive) as zf:
        destination.mkdir(parents=True, exist_ok=True)
        for name in zf.namelist():
            if name.startswith(stem + "."):
                zf.extract(name, destination)
    shp = destination / f"{stem}.shp"
    if not shp.exists():
        raise FileNotFoundError(f"Missing {stem}.shp in {archive}")
    return shp


def write_lineage() -> None:
    entries = {}
    for key, source in SOURCES.items():
        path = VALIDATION / source["filename"] if source.get("validation") else RAW / source["filename"]
        entries[key] = {
            "source_url": source["url"],
            "path": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
    infra = RAW / "osm_goslar_infrastructure_overpass.json"
    entries["osm_infrastructure"] = {
        "source_url": "https://overpass-api.de/api/interpreter",
        "query": INFRA_QUERY,
        "path": str(infra.relative_to(ROOT)),
        "bytes": infra.stat().st_size,
        "sha256": sha256(infra),
        "licence": "ODbL, (c) OpenStreetMap contributors",
    }
    derived = RAW / "osm_goslar_infrastructure_candidates.gpkg"
    entries["osm_infrastructure"]["derived_geopackage"] = str(derived.relative_to(ROOT))
    payload = {
        "dataset_id": "goslar_official_hydrology_and_flood_data",
        "access_date": date.today().isoformat(),
        "claim_level": "validation_candidate/context",
        "enters_pim_score": False,
        "sources": entries,
    }
    (OUT / "source_lineage.json").write_text(json.dumps(payload, indent=2) + "\n")


def write_infrastructure_candidates(source: Path) -> None:
    payload = json.loads(source.read_text(encoding="utf-8"))
    rows = []
    for element in payload.get("elements", []):
        tags = element.get("tags", {})
        facility = (
            tags.get("amenity")
            or tags.get("railway")
            or tags.get("power")
            or tags.get("man_made")
        )
        if facility not in INFRA_CLASSES:
            continue
        center = element.get("center", element)
        if element.get("type") == "node":
            center = element
        if center.get("lat") is None or center.get("lon") is None:
            continue
        rows.append(
            {
                "osm_type": element.get("type", ""),
                "osm_id": element.get("id", ""),
                "facility_class": facility,
                "name": tags.get("name", ""),
                "operator": tags.get("operator", ""),
                "tags": json.dumps(tags, ensure_ascii=False, sort_keys=True),
                "geometry": gpd.points_from_xy([center["lon"]], [center["lat"]])[0],
            }
        )
    candidates = gpd.GeoDataFrame(rows, crs="EPSG:4326", geometry="geometry")
    destination = RAW / "osm_goslar_infrastructure_candidates.gpkg"
    candidates.to_file(destination, driver="GPKG", layer="osm_infrastructure_candidates")
    if candidates.empty:
        raise RuntimeError("No infrastructure candidates matched the accepted classes")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--osm-json", type=Path, help="Reuse an existing Overpass JSON snapshot")
    args = parser.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    VALIDATION.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    for source in SOURCES.values():
        path = VALIDATION / source["filename"] if source.get("validation") else RAW / source["filename"]
        download(source["url"], path)

    infra_path = RAW / "osm_goslar_infrastructure_overpass.json"
    if args.osm_json:
        if not infra_path.exists():
            shutil.copy2(args.osm_json, infra_path)
    else:
        import urllib.parse
        import urllib.request

        if not infra_path.exists():
            data = urllib.parse.urlencode({"data": INFRA_QUERY}).encode()
            with urllib.request.urlopen("https://overpass.kumi.systems/api/interpreter", data=data, timeout=300) as r:
                infra_path.write_bytes(r.read())

    write_infrastructure_candidates(infra_path)

    with tempfile.TemporaryDirectory() as td:
        tmpdir = Path(td)
        basin_shp = extract_shapefile(RAW / SOURCES["basins"]["filename"], "DrainBasin_Waterbody_LOCAL", tmpdir / "basins")
        focus = gpd.read_file(ROOT / "outputs/goslar_focus_boundary/goslar_focus_boundary.gpkg").to_crs(32632)
        focus_geom = focus.geometry.union_all()
        context_geom = focus_geom.buffer(12000)

        basins = gpd.read_file(basin_shp).to_crs(32632)
        basins["overlap_km2"] = basins.geometry.intersection(focus_geom).area / 1e6
        selected = basins[basins["overlap_km2"] > 0].copy()
        selected["source_dataset"] = "NLWKN Umweltkarten WRRL DrainBasin_Waterbody_LOCAL"
        selected.to_file(OUT / "goslar_wfd_drainage_basins_focus_overlap.gpkg", driver="GPKG")

        hazard_parts = []
        for key in ("oker_hazard", "innerste_hazard"):
            stem = "Oker" if key == "oker_hazard" else "Innerste"
            with zipfile.ZipFile(RAW / SOURCES[key]["filename"]) as zf:
                names = [n for n in zf.namelist() if n.endswith("Grenze.shp")]
                if len(names) != 3:
                    raise RuntimeError(f"Expected three hazard boundary layers in {key}, got {names}")
                extract_dir = tmpdir / key
                extract_dir.mkdir()
                for name in names:
                    prefix = Path(name).stem
                    for suffix in (".shp", ".shx", ".dbf", ".prj", ".cpg"):
                        full = prefix + suffix
                        if full in zf.namelist():
                            zf.extract(full, extract_dir)
            for shp in sorted(extract_dir.glob("*Grenze.shp")):
                layer = gpd.read_file(shp).to_crs(32632)
                layer["overlap_context_km2"] = layer.geometry.intersection(context_geom).area / 1e6
                keep = layer[layer["overlap_context_km2"] > 0].copy()
                keep["source_dataset"] = f"NLWKN HWRM-RL {stem}"
                keep["source_archive"] = SOURCES[key]["filename"]
                hazard_parts.append(keep)
        hazard = gpd.GeoDataFrame(gpd.pd.concat(hazard_parts, ignore_index=True), crs="EPSG:32632")
        hazard.to_file(OUT / "goslar_hwrm_flood_hazard_boundaries_12km.gpkg", driver="GPKG")

    write_lineage()
    print(OUT / "source_lineage.json")


if __name__ == "__main__":
    main()
