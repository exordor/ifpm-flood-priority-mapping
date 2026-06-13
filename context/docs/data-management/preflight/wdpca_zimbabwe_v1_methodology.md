# Download Preflight: WDPCA Zimbabwe V1 Methodology Evidence

Status: closed for V1 evidence sweep download and processing.

## Scope

- [x] The dataset has a clear project purpose: official protected/conserved-area evidence.
- [x] The required study area is known: V1 working catchment and Zimbabwe context.
- [x] The expected scope is one Zimbabwe GeoPackage, not a global WDPCA mirror.
- [x] The expected disk footprint is acceptable.

## Access And Licence

- [x] Source URL and HDX API record are recorded in the registry note.
- [x] Product/version is recorded.
- [x] Licence or citation requirement must be cited before public release.
- [x] Account, registration, approval, or payment requirements are not expected for HDX download.
- [x] Credentials, cookies, tokens, and private links will not be committed.

## Destination

- [x] Raw data will go under `data/raw/wdpca_zimbabwe_v1_methodology/`.
- [x] Temporary downloads will go under `data/tmp/wdpca_zimbabwe_v1_methodology/`.
- [x] Processed summaries will go under `outputs/`.
- [x] No real downloaded data will be copied into `context/` or `ifpm-flood-pipeline/`.

## Safety Check

- [x] The target path is ignored by Git.
- [x] The command will not overwrite unrelated local data.
- [x] The output will be labelled as protected-area context, not flood-risk evidence.

## Completion Evidence

- Raw file:
  `data/raw/wdpca_zimbabwe_v1_methodology/protected_conserved_areas_wdpca.gpkg`.
- Raw manifest:
  `outputs/v1_full_methodology_evidence_sweep/source_manifest.csv`.
- File size: 733,184 bytes.
- SHA-256: `5ea5be5ce3bf5efb741157eaa927d54afdac89d6293e9a9b02e893b6d64d65b3`.
- Processed output:
  `outputs/v1_full_methodology_evidence_sweep/v1_wdpca_protected_area_summary.csv`.
- Result: 2 protected/conserved-area polygons overlap V1; 0 points overlap V1.
