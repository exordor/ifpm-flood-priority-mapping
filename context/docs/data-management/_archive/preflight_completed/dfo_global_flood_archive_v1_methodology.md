# Download Preflight: DFO Global Flood Archive V1 Methodology Evidence

Status: closed for Zimbabwe-level historical context download and processing.

## Scope

- [x] The dataset has a clear project purpose: historical/global flood-event context.
- [x] The required study area is known: V1 working catchment and Zimbabwe context.
- [x] The expected scope should be a global archive file or V1/Zimbabwe-screened subset, not
  unrelated flood imagery.
- [x] A stable HDX direct resource URL is available and downloaded.

## Access And Licence

- [x] Source URL and HDX API record are recorded in the registry note.
- [x] Product description is recorded.
- [x] Licence or citation requirement must be cited before public release.
- [x] Account, registration, approval, or payment requirements are not expected from the page.
- [x] Credentials, cookies, tokens, and private links will not be committed.

## Destination

- [x] Raw data will go under `data/raw/dfo_global_flood_archive_v1_methodology/`.
- [x] Temporary downloads will go under `data/tmp/dfo_global_flood_archive_v1_methodology/`.
- [x] Processed summaries will go under `outputs/`.
- [x] No real downloaded data will be copied into `context/` or `ifpm-flood-pipeline/`.

## Safety Check

- [x] The target path is ignored by Git.
- [x] The original DFO `temp` archive path was unstable from local curl, but HDX direct download
  was stable.
- [x] The output will be labelled as historical context, not local flood-risk validation.

## Completion Evidence

- Raw file:
  `data/raw/dfo_global_flood_archive_v1_methodology/wlf_nhr_fl_dfomasterlist_20190418.zip`.
- Raw manifest:
  `outputs/v1_full_methodology_evidence_sweep/source_manifest.csv`.
- File size: 610,578 bytes.
- SHA-256: `976f0904c603ba31e8aa62f6d1b55cec4c153be783495593ed247d01629ffe09`.
- Processed output:
  `outputs/v1_full_methodology_evidence_sweep/v1_dfo_zimbabwe_flood_events.csv`.
- Result: 9 Zimbabwe-related records, 3 valid event points, 0 valid event points inside V1 plus
  one degree.
