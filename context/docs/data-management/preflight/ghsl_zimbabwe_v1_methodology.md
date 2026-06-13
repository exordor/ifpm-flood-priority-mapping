# Download Preflight: GHSL Zimbabwe V1 Methodology Evidence

Status: closed for V1 evidence sweep download and processing.

## Scope

- [x] The dataset has a clear project purpose: socioeconomic exposure and built-up settlement
  cross-check.
- [x] The required study area is known: V1 working catchment.
- [x] The expected disk footprint is acceptable for two Zimbabwe rasters.
- [x] The download is not a broad global mirror.

## Access And Licence

- [x] Source URL is recorded in the registry note.
- [x] Product/version is recorded.
- [x] Licence or citation requirement must be cited before public release.
- [x] Account, registration, approval, or payment requirements are not expected.
- [x] Credentials, cookies, tokens, and private links will not be committed.

## Destination

- [x] Raw data will go under `data/raw/ghsl_zimbabwe_v1_methodology/`.
- [x] Temporary downloads will go under `data/tmp/ghsl_zimbabwe_v1_methodology/`.
- [x] Processed summaries will go under `outputs/`.
- [x] No real downloaded data will be copied into `context/` or `ifpm-flood-pipeline/`.

## Safety Check

- [x] The target path is ignored by Git.
- [x] The command will not overwrite unrelated local data.
- [x] Partial downloads can be identified by `.part` suffix and retried.
- [x] The output will be labelled as exposure cross-check, not accepted vulnerability truth.

## Completion Evidence

- Raw files:
  - `data/raw/ghsl_zimbabwe_v1_methodology/ghs_built_s_e2025_r2023a_54009_100_v1_0_zwe.tif`
  - `data/raw/ghsl_zimbabwe_v1_methodology/ghs_pop_e2025_r2023a_54009_100_v1_0_zwe.tif`
- Raw manifest:
  `outputs/v1_full_methodology_evidence_sweep/source_manifest.csv`.
- File sizes:
  - Built-up surface: 12,958,740 bytes.
  - Population: 37,893,059 bytes.
- SHA-256:
  - Built-up surface:
    `5f604c4992beb27df14f9f447caddef71540d8c17bbecce1a78d10c0b82820d1`
  - Population:
    `21ccdb3e2300cae9c739d0bbf2226f82c2bb738be6215f573554cf7318f7055e`
- Processed outputs:
  - `outputs/v1_full_methodology_evidence_sweep/rasters/v1_ghsl_built_surface_2025_native.tif`
  - `outputs/v1_full_methodology_evidence_sweep/rasters/v1_ghsl_population_2025_native.tif`
  - `outputs/v1_full_methodology_evidence_sweep/v1_ghsl_summary.csv`
