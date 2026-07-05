# Download Preflight: WorldPop Zimbabwe 2020 V1 Methodology Evidence

Status: closed for V1 evidence sweep download and processing.

## Scope

- [x] The dataset has a clear project purpose: socioeconomic exposure evidence.
- [x] The required study area is known: V1 working catchment.
- [x] The expected disk footprint is acceptable for one Zimbabwe raster.
- [x] The download is not a broad multi-year mirror.

## Access And Licence

- [x] Source URL is recorded in the registry note.
- [x] Product/version is recorded.
- [x] Licence or citation requirement must be cited before public release.
- [x] Account, registration, approval, or payment requirements are not expected.
- [x] Credentials, cookies, tokens, and private links will not be committed.

## Destination

- [x] Raw data will go under `data/raw/worldpop_zwe_2020_v1_methodology/`.
- [x] Temporary downloads will go under `data/tmp/worldpop_zwe_2020_v1_methodology/`.
- [x] Processed summaries will go under `outputs/`.
- [x] No real downloaded data will be copied into `context/` or `ifpm-flood-pipeline/`.

## Safety Check

- [x] The target path is ignored by Git.
- [x] The command will not overwrite unrelated local data.
- [x] Partial downloads can be identified by `.part` suffix and retried.
- [x] The output will be labelled as exposure proxy, not accepted vulnerability truth.

## Completion Evidence

- Raw file: `data/raw/worldpop_zwe_2020_v1_methodology/zwe_ppp_2020_UNadj.tif`.
- Raw manifest:
  `outputs/v1_full_methodology_evidence_sweep/source_manifest.csv`.
- File size: 192,412,178 bytes.
- SHA-256: `80f5a25269c85f5a4901beb6557936342c8eb90fae8f793fa47bbf3ddccf91c6`.
- Processed output:
  `outputs/v1_full_methodology_evidence_sweep/rasters/v1_worldpop_2020_unadj_native.tif`.
