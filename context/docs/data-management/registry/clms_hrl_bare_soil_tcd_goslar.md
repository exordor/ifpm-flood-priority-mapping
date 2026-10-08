# Dataset Registry: CLMS HRL bare-soil and tree-cover windows for Goslar

- Dataset id: `clms_hrl_bare_soil_tcd_goslar`
- Status: acquisition in progress via CLMS API background queue (2026-08-14/15); not yet entered into any PIM score.
- Claim level: `diagnostic_only` candidate source for the LU criterion (bare soil and vegetation-loss evidence), replacing the rejected Sentinel-2 MBI candidate for model integration only after coverage and QA checks.
- Portal: Copernicus Land Monitoring Service API (`land.copernicus.eu/api`), authenticated with the project API token (`data/tmp/clms_token_ifpm.json`).
- Access date: 2026-08-14 (requests submitted), download pending on queue.
- Licence: Copernicus Programme data terms; retain `Contains modified Copernicus Sentinel/CLMS data` attribution as applicable.

## Products and request parameters

1. HRL VLCC Bare Soil After 2017-present (10 m, Europe, yearly): dataset UID `bb6a2f6a0eca45b1b46ce83364fd6b6b`, download info id `c8f6d613-6e80-43ef-a361-12e660004939`; years 2017-2024.
2. HRL VLCC Tree Cover Density 2018-present (10 m, Europe, yearly): dataset UID `f954d06dfb5442b4910f0ccea9070917`, download info id `b119df47-079d-4d28-bda5-0748477a1053`; years 2018 and 2024.

- Output: Geotiff, EPSG:3035, bbox-cropped.
- Request bounding box (EPSG:4326, order N/E/S/W): [51.95, 10.50, 51.80, 10.30] (Goslar focus extent plus about 0.06 degree padding).
- The bare-soil layer reports the bare-soil period after the main crop season (percent of a year); it is not a binary bare-ground mask. TCD is percent tree cover; the 2018-to-2024 difference is the candidate vegetation-loss indicator.
- Source file inventory (full-tile COG manifest, public): `https://csv.dataspace.copernicus.eu/CLMS/landcover_landuse/cropping_patterns/clms_vlcc_bare-soil-after_europe_10m_yearly_v1/clms_vlcc_bare-soil-after_europe_10m_yearly_v1_cog.csv` and the equivalent `tree_cover_density/..._cog.csv`.

## Download routing

- Direct S3 access to `s3://eodata/CLMS/...` requires CDSE credentials (anonymous access returns 401/403), so the CLMS API background queue is used: `POST /api/@datarequest_post` (5-item queue cap) then poll `GET /api/@datarequest_search?status=Finished_ok`.
- Tooling: `bin/acquire/pull_goslar_clms_hrl.py` (submit / status / fetch / qa, resumable via `data/tmp/clms_hrl_tasks.json`).
- Expected local footprint: bbox crops only (order 1-20 MB per year), stored under `data/raw/clms_hrl_bare_soil_goslar/<year>/` and `data/raw/clms_hrl_tcd_goslar/<year>/`.

## QA and integration boundary

- After download: SHA-256 per zip, rasterio open check, coverage of the focus extent, value ranges (bare soil 0-100, TCD 0-100) and nodata fraction are recorded in `hrl_diagnostics.json` per product directory.
- Integration into the LU criterion is a chain-level decision (component reweighting), not automatic. The candidate does not change the `diagnostic_only` status of the Goslar chain.
- Known limitation: `Bare Soil After` is an agricultural bare-soil indicator; it does not by itself resolve the Sentinel MBI false positives over built and water classes. Pair with TCD change and land cover when used in scoring.

## 2026-08-17 direct CDSE update

- A CDSE S3 credential was created through the logged-in CDSE account and stored
  privately under `data/tmp/cdse_s3_credentials.json` (not committed).
- Direct access works against endpoint `https://eodata.dataspace.copernicus.eu`,
  bucket `eodata`.
- The 2024 Bare Soil After tiles `E43N31` and `E43N32` were downloaded and
  mosaicked under `data/raw/clms_hrl_bare_soil_goslar_official_basin/2024/`.
- Reproducible command:
  `.venv/bin/python bin/acquire/pull_goslar_clms_bare_soil_direct.py`
- Provisional chain QA: 166,105 / 170,882 official-basin 30 m cells valid;
  8,941 cells non-zero; 2nd percentile 0 and 98th percentile 59 percent-of-year.
  Output:
  `outputs/esa_worldcover_2021_goslar/c_factor/clms_bare_soil_after_2024_goslar_official_basin_30m.tif`
- This layer now replaces the all-zero WorldCover bare-soil proxy in the active
  Goslar chain while preserving the Secocha weight contract. The background
  queue remains pending for the full 2017-2024 yearly series and TCD change.
- 2026-08-18 update: the direct CDSE path was extended to all eight Bare Soil
  After years, 2017-2024 (16 source tiles plus annual mosaics). Per-year
  30 m diagnostics are recorded in
  `clms_bare_soil_after_series_diagnostics.json`; valid coverage is 96.2-98.0%.
- 2026-08-18 TCD update: `CLMS_HRLVLCC_TCD` tiles for 2018 and 2024 were
  downloaded directly and mosaicked. The active vegetation-loss indicator is
  now the positive percent-point TCD decline between 2018 and 2024:
  `clms_tcd_vegetation_loss_2018_2024_goslar_official_basin_30m.tif`.
  It has 170,882 valid cells and 94,552 non-zero cells. This replaces the
  single-year Bare Soil After indicator in the active LU component and is the
  intended semantic match for `bare_soil_vegetation_loss`.
