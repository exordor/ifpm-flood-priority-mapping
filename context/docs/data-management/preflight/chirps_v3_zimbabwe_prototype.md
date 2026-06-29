# Download Preflight: CHIRPS v3 Zimbabwe Prototype

Status: closed for controlled V1 rainfall-sensitivity comparison download and native/zonal
diagnostics. This does not authorize final flood-risk interpretation or treating CHIRPS as native
30 m rainfall evidence.

## Scope

- [x] The dataset has a clear project purpose: rainfall baseline.
- [x] The required study area is known at project level: Upper Mzingwane prototype slice.
- [x] The required temporal window is selected for comparison, not final modelling choice.
- [x] The CHIRPS v3 product type and timestep are selected for comparison.
- [x] The expected disk footprint is acceptable for the scoped comparison.
- [x] The download is not a broad mirror; intended scope is a selected temporal window only.

Selected comparison scope:

- Annual Africa GeoTIFFs: 1981-2024.
- Monthly Africa GeoTIFFs: November-March rainy seasons 1981/82-2023/24.
- Pentad Africa GeoTIFFs: November-March rainy seasons 2019/20-2023/24.
- Daily RNL COGs: 2023-11-01 to 2024-03-31, clipped to the V1 bounding box plus small padding.
- Output use: native CHIRPS grid diagnostics, V1 zonal summaries, and labelled
  diagnostic/provisional/sensitivity rainfall scenarios.
- Scale rule: any coarse-to-reference-grid resampling must record native resolution, target grid,
  resampling method, effective-resolution warning, and claim/status level.

## Access And Licence

- [x] Source URL or portal is recorded in the registry note.
- [x] Product/version is recorded.
- [x] Licence, terms, or citation requirements are checked at CHIRPS v3 page level.
- [x] Account, registration, approval, or payment requirements are documented.
- [x] Credentials, cookies, tokens, and private links will not be committed.

## Destination

- [x] Raw downloaded data will go under `data/raw/chirps_v3_zimbabwe_prototype/`.
- [x] Temporary downloads will go under `data/tmp/chirps_v3_zimbabwe_prototype/`.
- [x] Validation records are not part of this dataset.
- [x] Processed maps, diagnostics, and model outputs will go under `outputs/`.
- [x] Release bundles will go under `exports/` only as private/local bundles.
- [x] No real downloaded data will be copied into `context/` or `ifpm-flood-pipeline/`.

## Registry

- [x] A dataset registry note exists.
- [x] The note states this is reusable if the prototype proceeds.
- [x] The note includes source, product/version, access date, destination, and use.
- [x] The note includes licence/access constraints.
- [x] The note will include checksum or file-size evidence after download.
- [x] The note identifies checksum scope and expected/actual files.

## Safety Check

- [x] The target path is ignored by Git.
- [x] The command will not overwrite unrelated local data; script reuses existing files and writes
  only under `data/raw/chirps_v3_zimbabwe_prototype/`.
- [x] Partial or failed downloads can be identified and cleaned.
- [x] Partial path, attempt status, failure reason, and cleanup decision will be recorded.
- [x] The handoff will state that CHIRPS is a comparison input only, not a flood-risk result.

## Completion Evidence

- Download plan:
  `outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/chirps_v1_download_plan.csv`.
- Raw manifest:
  `outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/chirps_v1_raw_file_manifest.csv`.
- Actual inputs: 561 files, 1,837,685,335 bytes, all with SHA-256.
- Inventory check: 561/561 files readable by `rasterio`; all are `EPSG:4326` at approximately
  `0.05 x 0.05` degrees.
- Rainfall comparison outputs:
  `outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/v1_rainfall_metric_summary.csv`
  and `outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/mentor_v1_chirps_rainfall_comparison_board.png`.

Remaining blocked claims:

- Do not describe CHIRPS-derived products as native 30 m rainfall evidence.
- Do not run final intervention-priority mapping or final flood-risk interpretation from this
  comparison package alone.
- Do not use this package as the sole authority for final rainfall/R-factor choice.
