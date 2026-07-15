# Dataset Registry: SRTM 1 Arc-Second Southern Peru Arequipa Region

Status: downloaded and processed for Arequipa Region terrain diagnostics in the southern
Peru comparison catchment.

## Dataset Identity

- Dataset id: `srtm_1arcsec_peru_pilot`
- Short name: SRTM 1 Arc-Second Global
- Data class: `LOCAL_DATA`
- Reusable download: yes, if the Peru side proceeds
- Project role: terrain baseline for Arequipa Region elevation, slope, and hydrological derivatives
- Study area: Arequipa Region (`HYBAS_ID=6070641200`, 2745.4 km2), a Pacific-slope
  catchment in Arequipa Region, mainly the Vitor-La Joya-Santa Rita de Siguas
  area west of Arequipa city
- Spatial unit or mask: Arequipa Region boundary, the Peru analogue of the Zimbabwe V1 working boundary;
  Arequipa Region is NOT a research-selected boundary and will be replaced if the mentor names a Peru site
- Temporal coverage: SRTM mission acquisition period in February 2000

## Source And Access

- Source organization: USGS EROS original product; ESA STEP auxdata public mirror used for tile
  download (same source as the Zimbabwe prototype)
- Source URL or portal:
  - Product DOI: `https://doi.org/10.5066/F7PR7TFT`
  - Download mirror used: `https://step.esa.int/auxdata/dem/SRTMGL1/`
- Product/version: Shuttle Radar Topography Mission 1 Arc-Second Global
- DOI: `10.5066/F7PR7TFT`
- Access date: 2026-06-30
- Access method: direct HTTPS download from ESA STEP auxdata mirror; no login required
- Licence or terms: cite the SRTM 1 Arc-Second Global DOI and the mirror source used; do not
  redistribute raw files in public releases without a separate public-release clearance
- Account, registration, or approval needed: none
- Redistribution allowed: not approved for this project handoff; raw data remains local-only

## Download Plan

- Intended destination: `data/raw/srtm_1arcsec_peru_pilot/`
- Expected file types: zipped SRTMGL1 `.hgt` tiles
- Source artifact names: `S17W072.SRTMGL1.hgt.zip`, `S17W073.SRTMGL1.hgt.zip`
- Arequipa Region preflight bbox EPSG:4326 with buffer: covers the Arequipa Region pacific-slope catchment
- Expected file count: 2 SRTM 1x1 degree tiles
- Download command or manual steps:
  `.venv/bin/python bin/acquire/plan_srtm_tiles_for_peru_pilot.py` then
  `.venv/bin/python bin/factors/preprocess_srtm_peru_pilot_dem.py`
- Rate limits or quotas: none encountered
- Authentication handling: no credentials used

## Download Attempt State

- Attempt status: completed
- Attempt date: 2026-06-30
- Archive state: two ZIP source archives stored under `data/raw/srtm_1arcsec_peru_pilot/`
- Extraction state: extracted and mosaicked into the Arequipa Region DEM
- Cleanup/disposition: source archives and checksums retained

## Verification

- Download completed: yes
- Verification date: 2026-06-30
- Checksum algorithm: SHA-256
- Checksum values:

| Tile | Bytes | SHA-256 | Source file |
|---|---:|---|---|
| `S17W072` | 14,789,976 | `1aa455092c43c4fed256c21a47f3d84c6db40533e9402f12f63eb468e8f68f3e` | `S17W072.SRTMGL1.hgt.zip` |
| `S17W073` | 9,807,568 | `1ea7c09bf7d22feabee3cbed1b678201b135e48510f4e7bcb3a3dc7c69e8b375` | `S17W073.SRTMGL1.hgt.zip` |

- File-count evidence: 2 planned tiles downloaded
- CRS or georeferencing checked: yes; Arequipa Region DEM reprojected to EPSG:32718 (UTM 18S), 30 m
- Geometry/raster integrity checked: yes; elevation 144.9-3188.3 m, valid fraction 0.4506
- Licence/terms accepted: no credentialed terms accepted; public-release redistribution not
  approved

## Processing And Use

- Raw data path: `data/raw/srtm_1arcsec_peru_pilot/`
- Derived output path: `outputs/srtm_1arcsec_peru_pilot/`
- Scripts or commands used:
  `bin/acquire/plan_srtm_tiles_for_peru_pilot.py`,
  `bin/factors/preprocess_srtm_peru_pilot_dem.py`,
  `bin/factors/derive_peru_pilot_slope.py`,
  `bin/factors/derive_peru_pilot_hydrology.py`,
  `bin/factors/derive_peru_pilot_ls_factor.py`
- Reference-grid rule: `context/docs/data-management/peru_pilot_terrain_reference_grid_rule.md`
  (Arequipa Region DEM is the Peru reference grid, separate from Zimbabwe's EPSG:32735 reference)
- Known limitations: some SRTM tiles may contain voids; hydrological conditioning not guaranteed
- Replacement or update rule: replace if mentor names a specific Peru site or
  if a higher-resolution DEM is explicitly requested
- Validation role: terrain input only, not direct validation evidence

## Release Boundary

- May be committed: no
- May be used in public examples: no unless replaced by synthetic or approved sample data
- May be included in release archives: no unless explicitly approved
- Public-safe summary available: yes, this registry note without local files
