# Download Preflight: JRC Global Surface Water V1 Methodology Evidence

Status: closed for V1 evidence sweep download and processing.

## Scope

- [x] The dataset has a clear project purpose: remote-sensing water evidence for flood and
  environmental-sensitivity review.
- [x] The required study area is known: V1 working catchment inside `20E_20S`.
- [x] The expected disk footprint is acceptable for five JRC GSW tile layers.
- [x] The download is not a global mirror.

## Access And Licence

- [x] Source URL is recorded in the registry note.
- [x] Product/version is recorded.
- [x] Licence or citation requirement must be cited before public release.
- [x] Account, registration, approval, or payment requirements are not expected.
- [x] Credentials, cookies, tokens, and private links will not be committed.

## Destination

- [x] Raw data will go under `data/raw/jrc_global_surface_water_v1_methodology/`.
- [x] Temporary downloads will go under `data/tmp/jrc_global_surface_water_v1_methodology/`.
- [x] Processed summaries will go under `outputs/`.
- [x] No real downloaded data will be copied into `context/` or `ifpm-flood-pipeline/`.

## Safety Check

- [x] The target path is ignored by Git.
- [x] The command will not overwrite unrelated local data.
- [x] Partial downloads can be identified by `.part` suffix and retried.
- [x] The output will be labelled as water-history/context evidence, not observed flood-risk.

## Completion Evidence

- Raw directory: `data/raw/jrc_global_surface_water_v1_methodology/`.
- Raw manifest:
  `outputs/v1_full_methodology_evidence_sweep/source_manifest.csv`.
- File count: 5 GeoTIFF layers.
- Total file size: 81,504,552 bytes.
- Processed outputs:
  `outputs/v1_full_methodology_evidence_sweep/rasters/v1_jrc_gsw_*.tif`
  and `outputs/v1_full_methodology_evidence_sweep/v1_jrc_surface_water_summary.csv`.
