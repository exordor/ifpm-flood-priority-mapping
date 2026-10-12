# Dataset Registry: CHIRPS v3 Zimbabwe Prototype

Status: downloaded and processed for the V1 rainfall-sensitivity comparison.

## Dataset Identity

- Dataset id: `chirps_v3_zimbabwe`
- Short name: CHIRPS v3
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

## Acquisition

- Source artifact name:
  `outputs/zimbabwe_chirps_v3_rainfall/rainfall_comparison/zimbabwe_chirps_download_plan.csv`
- Download command or manual steps:
  1. Run `.venv/bin/python bin/acquire/plan_zimbabwe_chirps_rainfall_metrics.py`.
  2. Run `.venv/bin/python bin/acquire/download_zimbabwe_chirps_rainfall_inputs.py`.

## Download Record

- Attempt date: 2026-06-13
- Archive state: 561 local GeoTIFF inputs available
- Extraction state: not applicable; daily COG inputs were clipped directly to V1 bbox GeoTIFFs

## Files

- Checksum (SHA-256 preferred): per-file values recorded in
  `outputs/zimbabwe_chirps_v3_rainfall/rainfall_comparison/zimbabwe_chirps_raw_file_manifest.csv`
- Actual files or manifest:
  `outputs/zimbabwe_chirps_v3_rainfall/rainfall_comparison/zimbabwe_chirps_raw_file_manifest.csv`
- File size: 1,837,685,335 bytes across 561 inputs
- File-count evidence: 44 annual, 215 monthly, 150 pentad, and 152 daily V1 bbox files
- File-size evidence: raw data directory approximately 1.9 GB on disk
- CRS or georeferencing checked: yes; 561/561 files open with `rasterio`, CRS `EPSG:4326`,
  resolution approximately `0.05 x 0.05` degrees
- Geometry/raster integrity checked: yes, all scoped inputs were readable

## Processing And Use

- Raw data path: `data/raw/chirps_v3_zimbabwe/`
- Derived output path: `outputs/zimbabwe_chirps_v3_rainfall/`
- Scripts or commands used:
  - `.venv/bin/python bin/acquire/plan_zimbabwe_chirps_rainfall_metrics.py`
  - `.venv/bin/python bin/acquire/download_zimbabwe_chirps_rainfall_inputs.py`
  - `.venv/bin/python bin/investigate/compare_zimbabwe_chirps_rainfall_metrics.py`
    (Script removed 2026-10-11; recover with `git show cc4f247:bin/investigate/compare_zimbabwe_chirps_rainfall_metrics.py`.)
  - `.venv/bin/python bin/visualize/plot_zimbabwe_chirps_rainfall_comparison.py`
    (Script removed 2026-10-11; recover with `git show cc4f247:bin/visualize/plot_zimbabwe_chirps_rainfall_comparison.py`.)
- Standardization/preprocessing notes: keep CHIRPS at native rainfall scale and compute V1
  zonal summaries; do not resample to the V1 30 m terrain grid for pixel-level overlay
- Known limitations: 0.05 degree rainfall grid is much coarser than 30 m terrain layers; use
  aggregation or zonal summaries rather than treating pixels as equivalent
- Use: rainfall hazard input for the Zimbabwe V1 chain (Zimbabwe background only)
