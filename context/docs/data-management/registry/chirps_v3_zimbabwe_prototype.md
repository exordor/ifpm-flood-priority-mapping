# Dataset Registry: CHIRPS v3 Zimbabwe Prototype

Status: downloaded and processed for controlled V1 rainfall-sensitivity comparison. This does
not authorize AHP overlay, flood-risk interpretation, or 30 m CHIRPS resampling.

## Dataset Identity

- Dataset id: `chirps_v3_zimbabwe_prototype`
- Short name: CHIRPS v3
- Data class: `LOCAL_DATA`
- Reusable download: yes, if the prototype proceeds
- Project role: rainfall baseline for hazard indicators
- Study area: Zimbabwe / Upper Mzingwane Catchment prototype slice
- Spatial unit or mask: native CHIRPS grid clipped/masked to V1; V1 zonal summaries only
- Temporal coverage: comparison windows selected to cover annual background, rainy-season
  accumulation, anomaly, pentad extreme, and one recent daily-derived sensitivity check

## Source And Access

- Source organization: Climate Hazards Center, UC Santa Barbara
- Source URL or portal:
  - CHIRPS v3 page: `https://www.chc.ucsb.edu/data/chirps3`
  - CHC data repository: `https://data.chc.ucsb.edu/products/CHIRPS/v3.0/`
- Product/version: Climate Hazards Center Infrared Precipitation with Stations, version 3
- Repository DOI: `10.15780/G2JQ0P`
- Access date: 2026-06-13
- Access method: direct CHC repository or documented CHIRPS v3 access route
- Licence or terms: CHIRPS v3 page states Creative Commons Attribution 4.0 International
  License and public-domain waiver to the extent possible
- Citation requirement: cite CHIRPS v3 repository DOI and CHIRPS v3 Scientific Data paper
- Account, registration, or approval needed: none identified for CHC repository access
- Redistribution allowed: likely permitted under CC BY 4.0; confirm selected files and terms
  before release

## Download Plan

- Intended destination: `data/raw/chirps_v3_zimbabwe_prototype/`
- Expected file types: CHIRPS v3 final Africa GeoTIFFs plus clipped daily RNL COG-derived V1
  bbox GeoTIFFs
- Source artifact name:
  `outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/chirps_v1_download_plan.csv`
- Expected file count: 561 planned inputs
- Expected byte size: controlled but non-trivial; annual/monthly/pentad Africa files plus small
  daily V1 bbox clips, not a full daily mirror
- Download command or manual steps:
  1. Run `.venv/bin/python bin/plan_chirps_v1_rainfall_metrics.py`.
  2. Run `.venv/bin/python bin/download_chirps_v1_rainfall_inputs.py`.
  3. Record filenames, date range, size, and SHA-256 in the raw file manifest.
- Rate limits or quotas: unknown; avoid broad mirror downloads
- Authentication handling: no credentials expected
- Temporary path, if any: `data/tmp/chirps_v3_zimbabwe_prototype/`
- Cleanup needed after extraction: remove failed partials and keep only selected temporal window

## Download Attempt State

- Attempt status: completed for scoped V1 rainfall-sensitivity comparison
- Attempt date: 2026-06-13
- Failure reason, if any: not applicable
- Partial path, if any: none
- Archive state: 561 local GeoTIFF inputs available
- Extraction state: not applicable; daily COG inputs were clipped directly to V1 bbox GeoTIFFs
- Retry or resume safe: yes; scripts reuse existing files
- Cleanup/disposition: not applicable
- Cleanup date: not applicable

## Verification

- Download completed: yes
- Verification date: 2026-06-13
- Checksum scope: source files selected for temporal window
- Checksum algorithm: SHA-256 preferred
- Checksum command: `shasum -a 256 <file>`
- Checksum value: per-file values recorded in
  `outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/chirps_v1_raw_file_manifest.csv`
- Expected files or manifest:
  `outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/chirps_v1_download_plan.csv`
- Actual files or manifest:
  `outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/chirps_v1_raw_file_manifest.csv`
- Expected byte size: controlled scoped download, not a full CHIRPS mirror
- Actual byte size: 1,837,685,335 bytes across 561 inputs
- File-count evidence: 44 annual, 215 monthly, 150 pentad, and 152 daily V1 bbox files
- File-size evidence: raw data directory approximately 1.9 GB on disk
- CRS or georeferencing checked: yes; 561/561 files open with `rasterio`, CRS `EPSG:4326`,
  resolution approximately `0.05 x 0.05` degrees
- Geometry/raster integrity checked: yes, all scoped inputs were readable
- Licence/terms accepted: no interactive acceptance required; CHIRPS v3 page-level terms recorded

## Processing And Use

- Raw data path: `data/raw/chirps_v3_zimbabwe_prototype/`
- Derived output path: `outputs/chirps_v3_zimbabwe_prototype/`
- Scripts or commands used:
  - `.venv/bin/python bin/plan_chirps_v1_rainfall_metrics.py`
  - `.venv/bin/python bin/download_chirps_v1_rainfall_inputs.py`
  - `.venv/bin/python bin/compare_chirps_v1_rainfall_metrics.py`
  - `.venv/bin/python bin/plot_chirps_v1_rainfall_comparison.py`
- Standardization/preprocessing notes: keep CHIRPS at native rainfall scale and compute V1
  zonal summaries; do not resample to the V1 30 m terrain grid for pixel-level overlay
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
