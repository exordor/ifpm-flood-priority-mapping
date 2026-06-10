# Dataset Registry: SRTM 1 Arc-Second Zimbabwe Prototype

Status: planned; no data downloaded.

## Dataset Identity

- Dataset id: `srtm_1arcsec_zimbabwe_prototype`
- Short name: SRTM 1 Arc-Second Global
- Data class: `LOCAL_DATA`
- Reusable download: yes, if the prototype proceeds
- Project role: terrain baseline for elevation, slope, and hydrological derivatives
- Study area: Zimbabwe / Upper Mzingwane Catchment prototype slice
- Spatial unit or mask: catchment or HydroBASINS-compatible sub-catchment mask, pending
- Temporal coverage: SRTM mission acquisition period in February 2000

## Source And Access

- Source organization: USGS EROS
- Source URL or portal:
  - Product DOI: `https://doi.org/10.5066/F7PR7TFT`
  - Access portal: `https://earthexplorer.usgs.gov/`
- Product/version: Shuttle Radar Topography Mission 1 Arc-Second Global
- DOI: `10.5066/F7PR7TFT`
- Access date: 2026-06-10
- Access method: EarthExplorer search/download
- Licence or terms: USGS page describes public-domain media/open distribution; confirm terms in
  EarthExplorer before download
- Citation requirement: cite SRTM 1 Arc-Second Global DOI and USGS/EROS source
- Account, registration, or approval needed: EarthExplorer account may be required
- Redistribution allowed: likely public/open, but confirm during EarthExplorer workflow

## Download Plan

- Intended destination: `data/raw/srtm_1arcsec_zimbabwe_prototype/`
- Expected file types: raster tiles, likely GeoTIFF or product archive from EarthExplorer
- Source artifact name: tile names to be selected after boundary mask is fixed
- Expected file count: pending tile-selection query
- Expected byte size: pending tile-selection query
- Download command or manual steps:
  1. Open EarthExplorer.
  2. Select the Upper Mzingwane prototype area or bounding box.
  3. Choose SRTM 1 Arc-Second Global under Digital Elevation.
  4. Record selected tiles, terms, file count, and expected size before downloading.
- Rate limits or quotas: unknown; check EarthExplorer session
- Authentication handling: use browser/session only; do not record credentials
- Temporary path, if any: `data/tmp/srtm_1arcsec_zimbabwe_prototype/`
- Cleanup needed after extraction: remove duplicate archives or label retained source archives

## Download Attempt State

- Attempt status: planned
- Attempt date: not started
- Failure reason, if any: not applicable
- Partial path, if any: none
- Archive state: not downloaded
- Extraction state: not started
- Retry or resume safe: unknown until EarthExplorer workflow is known
- Cleanup/disposition: not applicable
- Cleanup date: not applicable

## Verification

- Download completed: no
- Verification date: not applicable
- Checksum scope: source archive or individual raster tiles, to be decided after download
- Checksum algorithm: SHA-256 preferred
- Checksum command: `shasum -a 256 <file>`
- Checksum value: not available
- Expected files or manifest: not available
- Actual files or manifest: not available
- Expected byte size: not available
- Actual byte size: not available
- File-count evidence: not available
- File-size evidence: not available
- CRS or georeferencing checked: no
- Geometry/raster integrity checked: no
- Licence/terms accepted: no

## Processing And Use

- Raw data path: `data/raw/srtm_1arcsec_zimbabwe_prototype/`
- Derived output path: `outputs/srtm_1arcsec_zimbabwe_prototype/`
- Scripts or commands used: none yet
- Standardization/preprocessing notes: clip to prototype boundary, check CRS, NoData, tile
  seams, voids, transform, and resolution before slope or flow derivatives
- Known limitations: some SRTM tiles may still contain voids; hydrological conditioning is not
  guaranteed
- Replacement or update rule: replace only if mentor supplies a more authoritative DEM or if
  Copernicus DEM comparison is explicitly requested
- Validation role: terrain input only, not direct validation evidence

## Release Boundary

- May be committed: no
- May be used in public examples: no unless replaced by synthetic or approved sample data
- May be included in release archives: no unless explicitly approved
- Public-safe summary available: yes, this registry note without local files
