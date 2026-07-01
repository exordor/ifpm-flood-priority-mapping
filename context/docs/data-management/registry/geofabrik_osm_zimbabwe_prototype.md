# Dataset Registry: Geofabrik OSM Zimbabwe Prototype

Status: downloaded and verified for visual review.

## Dataset Identity

- Dataset id: `geofabrik_osm_zimbabwe_prototype`
- Short name: Geofabrik Zimbabwe OSM extract
- Data class: `LOCAL_DATA`
- Reusable download: yes, if used for outlet exploration
- Project role: roads, bridges, settlements, waterways, and possible mine/quarry tags for
  candidate outlet evidence
- Study area: Zimbabwe / Upper Mzingwane candidate outlet discovery
- Spatial unit or mask: clip or filter to the candidate outlet search envelope after download
- Temporal coverage: current OSM extract at time of download

## Source And Access

- Source organization: Geofabrik / OpenStreetMap contributors
- Source URL or portal: `https://download.geofabrik.de/africa/zimbabwe.html`
- Product/version: latest Zimbabwe free extract available at download time
- Access date: checked 2026-06-12
- Access method: direct download
- Licence or terms: ODbL via OpenStreetMap / Geofabrik terms
- Citation requirement: cite OpenStreetMap contributors and Geofabrik extract route
- Account, registration, or approval needed: none expected for public extracts
- Redistribution allowed: governed by ODbL; do not redistribute raw extract without review

## Download Plan

- Intended destination: `data/raw/geofabrik_osm_zimbabwe_prototype/`
- Expected file types: `.gpkg.zip` plus local checksum
- Source artifact name: `zimbabwe-latest-free.gpkg.zip`, redirected on 2026-06-12 to
  `zimbabwe-260610-free.gpkg.zip`
- Expected file count: one archive plus local SHA-256 sidecar
- Expected byte size: `528811477` bytes from HTTP header on 2026-06-12
- Download command or manual steps: guarded `curl -L --fail --continue-at -` to a temporary
  path, verify byte size/checksum, then extract or inspect
- Rate limits or quotas: unknown
- Authentication handling: no credentials expected
- Temporary path, if any: `data/tmp/geofabrik_osm_zimbabwe_prototype/`
- Cleanup needed after extraction: remove failed partials and record manifest

## Download Attempt State

- Attempt status: complete
- Attempt date: 2026-06-12
- Failure reason, if any:
- Partial path, if any:
- Archive state: downloaded and verified
- Extraction state: complete
- Retry or resume safe: yes, with overwrite guards
- Cleanup/disposition:
- Cleanup date:

## Verification

- Download completed: yes
- Verification date: 2026-06-12
- Checksum scope: source archive
- Checksum algorithm: MD5 if using Geofabrik sidecar, otherwise SHA-256 local checksum
- Checksum command: `shasum -a 256 data/raw/geofabrik_osm_zimbabwe_prototype/zimbabwe-latest-free.gpkg.zip`
- Checksum value:
  `dcae916f091f6178ae6b182f4c2ff941777154a28f1aa740cb31765850fcacf2`
- Expected files or manifest: `zimbabwe.gpkg` and `README`
- Actual files or manifest: `data/raw/geofabrik_osm_zimbabwe_prototype/extraction_manifest.txt`
- Expected byte size: `528811477`
- Actual byte size: `528811477`
- File-count evidence: 2 extracted files listed in manifest
- File-size evidence: archive size matched HTTP header byte size
- CRS or georeferencing checked: yes, OGC:CRS84 / WGS84 source layers loaded and clipped
- Geometry/raster integrity checked: yes, 8657 OSM features intersect the review envelope after
  clipping
- Licence/terms accepted: yes for internal review use; ODbL redistribution requirements remain
  unreviewed

## Processing And Use

- Raw data path: `data/raw/geofabrik_osm_zimbabwe_prototype/`
- Derived output path: `outputs/_archive/superseded_outlet_exploration_2026-06/professional_outlet_review/`
- Scripts or commands used: guarded `curl`, `shasum -a 256`, `unzip`,
  `bin/_archive/superseded_outlet_exploration_2026-06/prepare_outlet_review_sources.py`
- Standardization/preprocessing notes: filter to search envelope before analysis
- Known limitations: OSM completeness varies; tags do not prove active mining or flood impact
- Replacement or update rule: replace with newer dated extract only if needed and documented
- Validation role: supporting evidence only

## Release Boundary

- May be committed: no
- May be used in public examples: no unless replaced by synthetic data
- May be included in release archives: no unless explicitly approved
- Public-safe summary available: yes
