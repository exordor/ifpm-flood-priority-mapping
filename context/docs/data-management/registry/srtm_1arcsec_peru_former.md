# Dataset Registry: SRTM 1 Arc-Second Southern Peru Arequipa Region

Status: downloaded 2026-06-30 and processed for terrain in the former Peru study area (frozen,
`peru_former`).

## Dataset Identity

- Dataset id: `srtm_1arcsec_peru_former`
- Short name: SRTM 1 Arc-Second Global
- Project role: terrain baseline for Arequipa Region elevation, slope, and hydrological derivatives
- Study area: former Peru study area (`HYBAS_ID=6070641200`, 2745.4 km2), a Pacific-slope
  catchment in Arequipa Region, mainly the Vitor-La Joya-Santa Rita de Siguas
  area west of Arequipa city
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
- Licence or terms: cite the SRTM 1 Arc-Second Global DOI and the mirror source used

## Acquisition

- Source artifact names: `S17W072.SRTMGL1.hgt.zip`, `S17W073.SRTMGL1.hgt.zip`
- Download command or manual steps:
  `.venv/bin/python bin/acquire/plan_peru_former_srtm_tiles.py` then
  (Script removed 2026-10-11; recover with `git show cc4f247:bin/acquire/plan_peru_former_srtm_tiles.py`.)
  `.venv/bin/python bin/factors/preprocess_peru_former_srtm_dem.py`

## Download Record

- Attempt date: 2026-06-30
- Archive state: two ZIP source archives stored under `data/raw/srtm_1arcsec_peru_former/`
- Extraction state: extracted and mosaicked into the Arequipa Region DEM

## Files

- Files:

| Tile | Bytes | SHA-256 | Source file |
|---|---:|---|---|
| `S17W072` | 14,789,976 | `1aa455092c43c4fed256c21a47f3d84c6db40533e9402f12f63eb468e8f68f3e` | `S17W072.SRTMGL1.hgt.zip` |
| `S17W073` | 9,807,568 | `1ea7c09bf7d22feabee3cbed1b678201b135e48510f4e7bcb3a3dc7c69e8b375` | `S17W073.SRTMGL1.hgt.zip` |

- File count: 2 tiles
- CRS or georeferencing checked: yes; Arequipa Region DEM reprojected to EPSG:32718 (UTM 18S), 30 m
- Geometry/raster integrity checked: yes; elevation 144.9-3188.3 m, valid fraction 0.4506

## Processing And Use

- Raw data path: `data/raw/srtm_1arcsec_peru_former/`
- Derived output path: `outputs/peru_former_pim_chain/`
- Scripts or commands used:
  `bin/acquire/plan_peru_former_srtm_tiles.py`,
  (Script removed 2026-10-11; recover with `git show cc4f247:bin/acquire/plan_peru_former_srtm_tiles.py`.)
  `bin/factors/preprocess_peru_former_srtm_dem.py`,
  `bin/factors/derive_peru_former_slope.py`,
  `bin/factors/derive_peru_former_hydrology.py`,
  `bin/factors/derive_peru_former_ls_factor.py`
- Reference grid: the reprojected DEM (EPSG:32718, 30 m) is the grid of the former Peru study area
- Known limitations: some SRTM tiles may contain voids; hydrological conditioning not guaranteed
- Use: terrain input for the former Peru study area chain
