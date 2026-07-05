# Download Preflight: ESA WorldCover 2021 V1 Methodology Evidence

Status: closed for V1 evidence sweep download and processing.

## Scope

- [x] The dataset has a clear project purpose: land use, environmental, and rehabilitation
  evidence candidates.
- [x] The required study area is known: V1 working catchment.
- [x] The expected disk footprint is acceptable for one WorldCover tile.
- [x] The download is not a broad mirror.

## Access And Licence

- [x] Source URL is recorded in the registry note.
- [x] Product/version is recorded.
- [x] Licence or citation requirement must be cited before public release.
- [x] Account, registration, approval, or payment requirements are not expected.
- [x] Credentials, cookies, tokens, and private links will not be committed.

## Destination

- [x] Raw data will go under `data/raw/esa_worldcover_2021_v1_methodology/`.
- [x] Temporary downloads will go under `data/tmp/esa_worldcover_2021_v1_methodology/`.
- [x] Processed maps and summaries will go under `outputs/`.
- [x] No real downloaded data will be copied into `context/` or `ifpm-flood-pipeline/`.

## Safety Check

- [x] The target path is ignored by Git.
- [x] The command will not overwrite unrelated local data.
- [x] Partial downloads can be identified by `.part` suffix and retried.
- [x] The output will be labelled as candidate evidence, not accepted model input.

## Completion Evidence

- Raw file:
  `data/raw/esa_worldcover_2021_v1_methodology/ESA_WorldCover_10m_2021_v200_S21E027_Map.tif`.
- Raw manifest:
  `outputs/v1_full_methodology_evidence_sweep/source_manifest.csv`.
- File size: 156,602,407 bytes.
- SHA-256: `9bc24ff959920471b288814b0cf2c1cb4b554a75b033730241caec9033e8aab7`.
- Processed outputs:
  `outputs/v1_full_methodology_evidence_sweep/rasters/v1_worldcover_2021_native_10m.tif`
  and `outputs/v1_full_methodology_evidence_sweep/v1_worldcover_class_area.csv`.
