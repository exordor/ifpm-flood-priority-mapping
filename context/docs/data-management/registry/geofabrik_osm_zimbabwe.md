# Dataset Registry: Geofabrik OSM Zimbabwe Prototype

Status: downloaded, verified, and used for V1 comparable road/water distance factors.

## Dataset Identity

- Dataset id: `geofabrik_osm_zimbabwe`
- Short name: Geofabrik Zimbabwe OSM extract
- Project role: roads, waterways and mine/quarry tags for the Zimbabwe V1 chain
- Study area: Zimbabwe / Upper Mzingwane prototype
- Temporal coverage: current OSM extract at time of download

## Source And Access

- Source organization: Geofabrik / OpenStreetMap contributors
- Source URL or portal: `https://download.geofabrik.de/africa/zimbabwe.html`
- Product/version: latest Zimbabwe free extract available at download time
- Access date: checked 2026-06-12
- Access method: direct download
- Licence or terms: ODbL via OpenStreetMap / Geofabrik terms
- Citation requirement: cite OpenStreetMap contributors and Geofabrik extract route

## Acquisition

- Source artifact name: `zimbabwe-latest-free.gpkg.zip`, redirected on 2026-06-12 to
  `zimbabwe-260610-free.gpkg.zip`
- Download command: `curl -L --fail --continue-at -`, then checksum and extract

## Download Record

- Attempt date: 2026-06-12
- Archive state: downloaded and verified
- Extraction state: complete

## Files

- Checksum (SHA-256):
  `dcae916f091f6178ae6b182f4c2ff941777154a28f1aa740cb31765850fcacf2`
- Actual files or manifest: `data/raw/geofabrik_osm_zimbabwe/extraction_manifest.txt`
- File size: 528,811,477 bytes
- File-count evidence: 2 extracted files listed in manifest. The unpacked copy under `extracted/` was removed on 2026-10-12 (byte-identical to the zip, which is kept).
- CRS or georeferencing checked: yes, OGC:CRS84 / WGS84 source layers loaded and clipped
- Geometry/raster integrity checked: yes, 8657 OSM features intersect the review envelope after
  clipping

## Processing And Use

- Raw data path: `data/raw/geofabrik_osm_zimbabwe/`
- Derived output path: `outputs/zimbabwe_terrain_hydrology_factors/comparable_distance_factors/`
- Script: `bin/factors/build_zimbabwe_comparable_distance_factors.py`; it reads the GeoPackage
  (Script removed 2026-10-11; recover with `git show cc4f247:bin/factors/build_zimbabwe_comparable_distance_factors.py`.)
  directly through GDAL `/vsizip/` without duplicating the 1.1 GB uncompressed file
- Standardization/preprocessing notes: read OSM roads and water features over a 25 km padded
  EPSG:32735 reference-grid envelope, rasterize on that padded 30 m grid, calculate Euclidean
  distance in kilometres, crop back to the reference grid, and preserve the V1 mask. The padding
  prevents edge cells from ignoring nearer mapped features immediately outside the study area.
- Known limitations: OSM completeness varies; tags do not prove active mining or flood impact
- Use: road and water distance factors for the Zimbabwe V1 chain (Zimbabwe background only)
