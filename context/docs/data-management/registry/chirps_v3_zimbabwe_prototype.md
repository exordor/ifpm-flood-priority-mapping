# Dataset Registry: CHIRPS v3 Zimbabwe Prototype

Status: planned; no data downloaded.

## Dataset Identity

- Dataset id: `chirps_v3_zimbabwe_prototype`
- Short name: CHIRPS v3
- Data class: `LOCAL_DATA`
- Reusable download: yes, if the prototype proceeds
- Project role: rainfall baseline for hazard indicators
- Study area: Zimbabwe / Upper Mzingwane Catchment prototype slice
- Spatial unit or mask: catchment or raster clip mask, pending
- Temporal coverage: select after prototype temporal window is chosen; source spans 1981 to
  near present

## Source And Access

- Source organization: Climate Hazards Center, UC Santa Barbara
- Source URL or portal:
  - CHIRPS v3 page: `https://www.chc.ucsb.edu/data/chirps3`
  - CHC data repository: `https://data.chc.ucsb.edu/products/CHIRPS/v3.0/`
- Product/version: Climate Hazards Center Infrared Precipitation with Stations, version 3
- Repository DOI: `10.15780/G2JQ0P`
- Access date: 2026-06-10
- Access method: direct CHC repository or documented CHIRPS v3 access route
- Licence or terms: CHIRPS v3 page states Creative Commons Attribution 4.0 International
  License and public-domain waiver to the extent possible
- Citation requirement: cite CHIRPS v3 repository DOI and CHIRPS v3 Scientific Data paper
- Account, registration, or approval needed: none identified for CHC repository access
- Redistribution allowed: likely permitted under CC BY 4.0; confirm selected files and terms
  before release

## Download Plan

- Intended destination: `data/raw/chirps_v3_zimbabwe_prototype/`
- Expected file types: GeoTIFF, NetCDF, BIL, or COG depending on selected product
- Source artifact name: pending timestep, product type, temporal window, and domain decision
- Expected file count: pending temporal window and file format
- Expected byte size: pending temporal window and file format
- Download command or manual steps:
  1. Choose CHIRPS v3 product type: final or preliminary.
  2. Choose timestep: monthly or annual preferred for first prototype summary.
  3. Choose domain or global/Africa subset route.
  4. Record filenames, date range, format, and expected size before downloading.
- Rate limits or quotas: unknown; avoid broad mirror downloads
- Authentication handling: no credentials expected
- Temporary path, if any: `data/tmp/chirps_v3_zimbabwe_prototype/`
- Cleanup needed after extraction: remove failed partials and keep only selected temporal window

## Download Attempt State

- Attempt status: planned
- Attempt date: not started
- Failure reason, if any: not applicable
- Partial path, if any: none
- Archive state: not downloaded
- Extraction state: not started
- Retry or resume safe: unknown until selected access route is tested
- Cleanup/disposition: not applicable
- Cleanup date: not applicable

## Verification

- Download completed: no
- Verification date: not applicable
- Checksum scope: source files selected for temporal window
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

- Raw data path: `data/raw/chirps_v3_zimbabwe_prototype/`
- Derived output path: `outputs/chirps_v3_zimbabwe_prototype/`
- Scripts or commands used: none yet
- Standardization/preprocessing notes: clip or aggregate rainfall to the prototype boundary only
  after temporal window, timestep, and product type are selected
- Known limitations: 0.05 degree rainfall grid is much coarser than 30 m terrain layers; use
  aggregation or zonal summaries rather than treating pixels as equivalent
- Replacement or update rule: replace or supplement if local rain-gauge or hydrometric evidence
  is approved for the prototype
- Validation role: rainfall hazard input only, not independent validation evidence

## Release Boundary

- May be committed: no
- May be used in public examples: no unless replaced by synthetic or approved sample data
- May be included in release archives: no unless explicitly approved
- Public-safe summary available: yes, this registry note without downloaded files

