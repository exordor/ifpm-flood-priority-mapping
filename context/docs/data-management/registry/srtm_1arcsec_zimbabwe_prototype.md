# Dataset Registry: SRTM 1 Arc-Second Zimbabwe Prototype

Status: downloaded and inventoried for controlled V1 terrain diagnostics only.

## Dataset Identity

- Dataset id: `srtm_1arcsec_zimbabwe_prototype`
- Short name: SRTM 1 Arc-Second Global
- Data class: `LOCAL_DATA`
- Reusable download: yes, if the prototype proceeds
- Project role: terrain baseline for elevation, slope, and hydrological derivatives
- Study area: Zimbabwe / Upper Mzingwane Catchment prototype slice
- Spatial unit or mask: V1 working boundary /
  `HB_L8_1081528840_full_l7_chain`, accepted with waiver for controlled prototype use
- Temporal coverage: SRTM mission acquisition period in February 2000

## Source And Access

- Source organization: USGS EROS original product; ESA STEP auxdata public mirror used for tile
  download
- Source URL or portal:
  - Product DOI: `https://doi.org/10.5066/F7PR7TFT`
  - Access portal: `https://earthexplorer.usgs.gov/`
  - Download mirror used: `https://step.esa.int/auxdata/dem/SRTMGL1/`
- Product/version: Shuttle Radar Topography Mission 1 Arc-Second Global
- DOI: `10.5066/F7PR7TFT`
- Access date: 2026-06-12
- Access method: direct HTTPS download from ESA STEP auxdata mirror; no login was required
- Licence or terms: cite the SRTM 1 Arc-Second Global DOI and the mirror source used; do not
  redistribute raw files in public releases without a separate public-release clearance
- Citation requirement: cite SRTM 1 Arc-Second Global DOI, USGS/EROS original source, and ESA
  STEP mirror access if reporting the local download path
- Account, registration, or approval needed: none encountered for the ESA STEP mirror; stop and
  defer to the user if a future source requires login
- Redistribution allowed: not approved for this project handoff; raw data remains local-only

## Download Plan

- Intended destination: `data/raw/srtm_1arcsec_zimbabwe_prototype/`
- Expected file types: raster tiles, likely GeoTIFF or product archive from EarthExplorer
- Source artifact names: `S22E028.SRTMGL1.hgt.zip`, `S22E029.SRTMGL1.hgt.zip`,
  `S21E028.SRTMGL1.hgt.zip`, `S21E029.SRTMGL1.hgt.zip`, `S20E028.SRTMGL1.hgt.zip`, and
  `S20E029.SRTMGL1.hgt.zip`
- V1 preflight bbox EPSG:4326 with 5 km buffer:
  `28.514098, -21.007996, 29.398052, -19.984062`
- Expected file count: 6 SRTM 1x1 degree tiles
- Expected byte size: bounded local download; actual source archive size is `41,162,741` bytes
  across six ZIP files.
- Download command or manual steps:
  `.venv/bin/python bin/download_srtm_v1_tiles.py`
- Rate limits or quotas: none encountered during the ESA STEP mirror download
- Authentication handling: no credentials, cookies, tokens, or private links were used
- Temporary path, if any: `data/tmp/srtm_1arcsec_zimbabwe_prototype/`
- Cleanup needed after extraction: remove duplicate archives or label retained source archives

## Download Attempt State

- Attempt status: completed
- Attempt date: 2026-06-12
- Failure reason, if any: not applicable
- Partial path, if any: none retained
- Archive state: six ZIP source archives stored under `data/raw/srtm_1arcsec_zimbabwe_prototype/`
- Extraction state: not extracted; inventory reads the `.hgt` members inside ZIP archives
- Retry or resume safe: yes, script skips already-present valid ZIP files
- Cleanup/disposition: temporary `.part` files were not retained
- Cleanup date: 2026-06-12

## Verification

- Download completed: yes
- Verification date: 2026-06-12
- Checksum scope: downloaded source ZIP archives
- Checksum algorithm: SHA-256 preferred
- Checksum command: `.venv/bin/python bin/download_srtm_v1_tiles.py` and
  `.venv/bin/python bin/inventory_srtm_v1_tiles.py`
- Checksum value: see `outputs/srtm_1arcsec_zimbabwe_prototype/srtm_raw_file_manifest.csv`
- Expected files or manifest:
  `outputs/v1_working_boundary/srtm_v1_tile_plan.csv`
- Actual files or manifest:
  `outputs/srtm_1arcsec_zimbabwe_prototype/srtm_raw_file_manifest.csv`
- Expected byte size: `<500 MB` pre-download disk guard
- Actual byte size: `41,162,741` bytes
- File-count evidence: 6 planned tiles in
  `outputs/v1_working_boundary/srtm_v1_tile_plan.csv`
- File-size evidence:
  `outputs/srtm_1arcsec_zimbabwe_prototype/srtm_raw_file_manifest.csv`
- CRS or georeferencing checked: yes; inventory reports `EPSG:4326`
- Geometry/raster integrity checked: yes; each archive opens as one `SRTMHGT` band
- Licence/terms accepted: no credentialed terms were accepted; public-release redistribution is
  still not approved

Downloaded file evidence:

| Tile | Bytes | SHA-256 | Source file |
|---|---:|---|---|
| `S22E028` | 6,005,782 | `b456c297a3f9ff0c75a03cc616ab8fc3a1e52a8ce94cfc05483183ba58f8c738` | `S22E028.SRTMGL1.hgt.zip` |
| `S22E029` | 6,715,196 | `aa8ad5daf9c9c155df900d24077907249d83bfda74ab3dc10e161eef70537b68` | `S22E029.SRTMGL1.hgt.zip` |
| `S21E028` | 7,754,907 | `6d53552260081fa24308bbf2cbad369379462aabc08f59534396f48ea3161238` | `S21E028.SRTMGL1.hgt.zip` |
| `S21E029` | 7,653,703 | `be04b8316c3c217ce4dead923255abd0fce1c18abfd026bf6ef8fc391b6a4ba5` | `S21E029.SRTMGL1.hgt.zip` |
| `S20E028` | 6,346,821 | `e1f2cb4051e056fd32582da3b4d122f860082e5e53c509f79152fe0b8627ab2a` | `S20E028.SRTMGL1.hgt.zip` |
| `S20E029` | 6,686,332 | `de5a4b3cf2ab11b4264920539f5b86ea25f081861050dc1baca15dd2d2d2b71b` | `S20E029.SRTMGL1.hgt.zip` |

## Processing And Use

- Raw data path: `data/raw/srtm_1arcsec_zimbabwe_prototype/`
- Derived output path: `outputs/srtm_1arcsec_zimbabwe_prototype/` for future terrain products;
  pre-download tile planning output is under `outputs/v1_working_boundary/`
- Scripts or commands used:
  `.venv/bin/python bin/plan_srtm_tiles_for_v1.py`,
  `.venv/bin/python bin/download_srtm_v1_tiles.py`,
  `.venv/bin/python bin/inventory_srtm_v1_tiles.py`,
  `.venv/bin/python bin/preprocess_srtm_v1_dem.py`,
  `.venv/bin/python bin/derive_srtm_v1_slope.py`, and
  `.venv/bin/python bin/plot_srtm_v1_terrain_qa.py`
- Standardization/preprocessing notes: V1 DEM and slope diagnostics now exist under
  `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/`; terrain standardization for
  scoring is not started
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
