# Dataset Registry: Geofabrik OSM Southern Peru Arequipa Region

Status: downloaded 2026-06-30 and processed for proximity criteria in the former Peru study area
(frozen, `peru_former`).

## Dataset Identity

- Dataset id: `geofabrik_osm_peru_former`
- Short name: Geofabrik Peru OSM extract
- Spatial unit or mask: clipped to the former Peru study area + 5 km buffer
- Temporal coverage: current OSM extract at time of download (2026-06-30)

## Source And Access

- Source organization: Geofabrik / OpenStreetMap contributors
- Source URL or portal: `https://download.geofabrik.de/south-america/peru.html`
- Direct source artifact:
  `https://download.geofabrik.de/south-america/peru-latest-free.shp.zip`
- Access method: direct public download (302 redirect to the actual file)
- Licence or terms: OpenStreetMap data, ODbL; Geofabrik extract.

## Download Record

- Access date: 2026-06-30
- Download command: `curl --fail --location --output peru-latest-free.shp.zip <url>`
- Raw destination: `data/raw/geofabrik_osm_peru_former/peru-latest-free.shp.zip`
- File size: 597,543,300 bytes (full Peru country extract)
- SHA-256: `e34517e410d30f0abde0c06210ec77663c6d6218f35672f0b51d91ef2242e209`
- Extraction: complete to `data/raw/geofabrik_osm_peru_former/extracted/` (20 shapefile layers)

## Used Layers (former Peru study area)

- `gis_osm_roads_free_1.shp` -> exposure_indicators proximity criterion (6210 features in
  Arequipa Region + 5km).
- `gis_osm_landuse_a_free_1.shp` -> mining_pressure proximity criterion (32 quarry/industrial
  polygons in Arequipa Region + 5km; stronger than Zimbabwe V1's 2 polygons).
- `gis_osm_places_free_1.shp` -> context only (208 places; not a scored criterion).

## Notes And Limits

- The mining proxy is OSM landuse quarry/industrial; it was later replaced by INGEMMET points
  (`ingemmet_catastro_minero_peru_former`).
- Road proximity is an access/exposure proxy, not observed flood vulnerability.
- Only the layers above are used.
