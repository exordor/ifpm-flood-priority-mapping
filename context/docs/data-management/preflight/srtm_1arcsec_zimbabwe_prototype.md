# Download Preflight: SRTM 1 Arc-Second Zimbabwe Prototype

Status: downloaded, inventoried, and preprocessed into controlled V1 DEM/slope diagnostics.

## Scope

- [x] The dataset has a clear project purpose: terrain baseline.
- [x] The required study area is known at project level: Upper Mzingwane prototype slice.
- [x] The exact boundary mask or bounding box is finalized for prototype-only use:
      V1 / `HB_L8_1081528840_full_l7_chain` with a 5 km buffer.
- [x] The temporal window is documented: static SRTM acquisition period.
- [x] The expected disk footprint is acceptable for a bounded local test: 6 SRTM 1x1 degree
      tiles with a conservative `<500 MB` pre-download disk guard; actual source archive size is
      `41,162,741` bytes.
- [x] The download is not a broad bulk mirror; intended scope is selected local tiles only.
- [x] Planned tiles are `S22E028`, `S22E029`, `S21E028`, `S21E029`, `S20E028`, and `S20E029`.
- [x] The six planned tiles were downloaded and no extra tiles were added.

## Access And Licence

- [x] Source URL or portal is recorded in the registry note.
- [x] Product/version is recorded.
- [x] Licence, terms, or citation requirements are flagged for source/citation confirmation.
- [x] Account, registration, approval, or payment requirements are documented; no login was
      encountered for the ESA STEP mirror.
- [x] Credentials, cookies, tokens, and private links will not be committed.

## Destination

- [x] Raw downloaded data will go under `data/raw/srtm_1arcsec_zimbabwe_prototype/`.
- [x] Temporary downloads will go under `data/tmp/srtm_1arcsec_zimbabwe_prototype/`.
- [x] Validation records are not part of this dataset.
- [x] Processed maps, diagnostics, and model outputs will go under `outputs/`.
- [x] Release bundles will go under `exports/` only as private/local bundles.
- [x] No real downloaded data will be copied into `context/` or `ifpm-flood-pipeline/`.

## Registry

- [x] A dataset registry note exists.
- [x] The note states this is reusable if the prototype proceeds.
- [x] The note includes source, product/version, access date, destination, and use.
- [x] The note includes licence/access constraints.
- [x] The note includes checksum and file-size evidence after download.
- [x] The note identifies checksum scope and expected/actual files.
- [x] Pre-download tile plan exists:
      `outputs/v1_working_boundary/srtm_v1_tile_plan.csv`.
- [x] Post-download raw manifest exists:
      `outputs/srtm_1arcsec_zimbabwe_prototype/srtm_raw_file_manifest.csv`.
- [x] Post-download raster inventory exists:
      `outputs/srtm_1arcsec_zimbabwe_prototype/srtm_tile_inventory.csv`.

## Safety Check

- [x] The target path is ignored by Git.
- [x] The next download command or manual copy must target only
      `data/raw/srtm_1arcsec_zimbabwe_prototype/` and must not overwrite unrelated local data.
- [x] Partial or failed downloads can be identified and cleaned.
- [x] Partial path, attempt status, failure reason, and cleanup decision will be recorded.
- [x] The handoff states that SRTM was downloaded only for terrain diagnostics and that no
      CHIRPS, overlay, or interpretation was performed.

## Post-Download Verification

- [x] Download completed on 2026-06-12.
- [x] Actual source archive count is 6.
- [x] Actual source archive bytes are `41,162,741`.
- [x] Every archive has a SHA-256 checksum in
      `outputs/srtm_1arcsec_zimbabwe_prototype/srtm_raw_file_manifest.csv`.
- [x] Every tile opens through rasterio as `SRTMHGT`, `EPSG:4326`, `3601 x 3601`, one band,
      `int16`, NoData `-32768`.
- [x] Coverage figure exists at
      `outputs/srtm_1arcsec_zimbabwe_prototype/srtm_tile_coverage_check.png`.
- [x] Raw download and inventory produced no slope, flow accumulation, AHP overlay, flood-risk
      map, or interpretation.
- [x] A later controlled preprocessing step produced V1 DEM and slope diagnostics only; it did
      not produce flow accumulation, AHP overlay, flood-risk map, or interpretation.

## Post-Preprocessing Verification

- [x] V1 DEM exists at
      `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif`.
- [x] V1 slope exists at
      `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_slope_degrees_utm35s_30m.tif`.
- [x] Both final rasters are `EPSG:32735`, `30 m`, single-band `float32`, NoData `-9999.0`.
- [x] Both final rasters have valid-cell fraction `1.0` inside V1.
