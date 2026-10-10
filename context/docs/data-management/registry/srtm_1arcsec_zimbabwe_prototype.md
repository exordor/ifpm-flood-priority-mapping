# Dataset Registry: SRTM 1 Arc-Second Zimbabwe Prototype

Status: downloaded and inventoried for V1 terrain diagnostics. Zimbabwe is background only.

## Dataset Identity

- Dataset id: `srtm_1arcsec_zimbabwe_prototype`
- Short name: SRTM 1 Arc-Second Global
- Project role: terrain baseline for elevation, slope, and hydrological derivatives
- Study area: Zimbabwe / Upper Mzingwane Catchment prototype slice
- Spatial unit or mask: V1 working boundary /
  `HB_L8_1081528840_full_l7_chain` (Zimbabwe prototype boundary)
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
- Licence or terms: cite the SRTM 1 Arc-Second Global DOI and the mirror source used
- Citation requirement: cite SRTM 1 Arc-Second Global DOI, USGS/EROS original source, and ESA
  STEP mirror access if reporting the local download path

## Acquisition

- Source artifact names: `S22E028.SRTMGL1.hgt.zip`, `S22E029.SRTMGL1.hgt.zip`,
  `S21E028.SRTMGL1.hgt.zip`, `S21E029.SRTMGL1.hgt.zip`, `S20E028.SRTMGL1.hgt.zip`, and
  `S20E029.SRTMGL1.hgt.zip`
- V1 bbox EPSG:4326 with 5 km buffer:
  `28.514098, -21.007996, 29.398052, -19.984062`
- Download command or manual steps:
  `.venv/bin/python bin/acquire/download_srtm_v1_tiles.py`

## Download Record

- Attempt date: 2026-06-12
- Archive state: six ZIP source archives stored under `data/raw/srtm_1arcsec_zimbabwe_prototype/`
- Extraction state: not extracted; inventory reads the `.hgt` members inside ZIP archives

## Files

- Manifest (bytes, SHA-256):
  `outputs/srtm_1arcsec_zimbabwe_prototype/srtm_raw_file_manifest.csv`
- File size: `41,162,741` bytes
- File count: 6 tiles
- CRS or georeferencing checked: yes; inventory reports `EPSG:4326`
- Geometry/raster integrity checked: yes; each archive opens as one `SRTMHGT` band

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
- Derived output path: `outputs/srtm_1arcsec_zimbabwe_prototype/`;
  tile plan under `outputs/v1_working_boundary/`
- Scripts or commands used:
  `.venv/bin/python bin/acquire/plan_srtm_tiles_for_v1.py`,
  `.venv/bin/python bin/acquire/download_srtm_v1_tiles.py`,
  `.venv/bin/python bin/acquire/inventory_srtm_v1_tiles.py`,
  `.venv/bin/python bin/factors/preprocess_srtm_v1_dem.py`,
  `.venv/bin/python bin/factors/derive_srtm_v1_slope.py`, and
  `.venv/bin/python bin/visualize/plot_srtm_v1_terrain_qa.py`
- Standardization/preprocessing notes: V1 DEM and slope diagnostics now exist under
  `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/`; terrain standardization for
  scoring is not started
- Known limitations: some SRTM tiles may still contain voids; hydrological conditioning is not
  guaranteed
- Use: terrain input for the Zimbabwe V1 chain
