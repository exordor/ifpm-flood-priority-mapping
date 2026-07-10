# Dataset Registry: Geofabrik OSM Southern Peru PE1

Status: downloaded and processed for PE1 proximity-criteria derivation. Same source family
and license as the already-downloaded Geofabrik Zimbabwe extract.

## Dataset Identity

- Dataset id: `geofabrik_osm_peru_pilot`
- Short name: Geofabrik Peru OSM extract
- Reusable download: yes, for PE1 mining/exposure proximity criteria
- Spatial unit or mask: clip to PE1 boundary + 5 km buffer after download
- Temporal coverage: current OSM extract at time of download (2026-06-30)

## Source And Access

- Source organization: Geofabrik / OpenStreetMap contributors
- Source URL or portal: `https://download.geofabrik.de/south-america/peru.html`
- Direct source artifact:
  `https://download.geofabrik.de/south-america/peru-latest-free.shp.zip`
- Access method: direct public download (302 redirect to the actual file)
- Licence or terms: OpenStreetMap data, ODbL; Geofabrik extract. Same license as the Zimbabwe
  Geofabrik extract already in use.
- Account, registration, or approval needed: none

## Download Record

- Access date: 2026-06-30
- Download command: `curl --fail --location --output peru-latest-free.shp.zip <url>`
- Raw destination: `data/raw/geofabrik_osm_peru_pilot/peru-latest-free.shp.zip`
- Actual size: `597543300` bytes (~597 MB, full Peru country extract)
- SHA-256: `e34517e410d30f0abde0c06210ec77663c6d6218f35672f0b51d91ef2242e209`
- Extraction: complete to `data/raw/geofabrik_osm_peru_pilot/extracted/` (20 shapefile layers)

## Used Layers (PE1)

- `gis_osm_roads_free_1.shp` -> exposure_indicators proximity criterion (6210 features in
  PE1 + 5km).
- `gis_osm_landuse_a_free_1.shp` -> mining_pressure proximity criterion (32 quarry/industrial
  polygons in PE1 + 5km; stronger than Zimbabwe V1's 2 polygons).
- `gis_osm_places_free_1.shp` -> context only (208 places; not a scored criterion).

## Notes And Limits

- The mining proxy is OSM landuse quarry/industrial, NOT official mining truth. INGEMMET/
  GEOCATMIN is the authoritative Peru mining cadastre (publicly accessible, identified but not
  yet processed) and is the upgrade path for the mining criterion.
- Road proximity is an access/exposure proxy, not observed flood vulnerability.
- Only PE1-relevant layers are used; the full country extract is kept under ignored `data/`.
