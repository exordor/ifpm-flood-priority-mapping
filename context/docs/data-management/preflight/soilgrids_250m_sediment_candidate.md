# Download Preflight: SoilGrids 250m Sediment Candidate

Status: DRAFT. Pre-download blockers not yet checked. No download authorized. Created as P2 R2.1
scaffolding. The `[ ]` items below must be checked, and Gate G5 authorization recorded, before any
real download attempt.

## Scope

- [ ] The dataset has a clear project purpose: USLE/RUSLE K-factor and soil-property context.
- [ ] The required study area is known: V1 bounding box and Zimbabwe context.
- [ ] The required properties/depths are known: clay, silt, sand, organic carbon at selected
      depths (to be finalized at authorization).
- [ ] The expected disk footprint is acceptable: tens to low hundreds of MB for a scoped subset.
- [ ] The download is not a broad bulk mirror: scoped to V1 bounding box.

## Access And Licence

- [ ] Source URL or portal is recorded in the registry note (ISRIC SoilGrids).
- [ ] Product/version is recorded.
- [ ] Licence, terms, or citation requirements are checked (CC BY 4.0; cite ISRIC).
- [ ] Account, registration, approval, or payment requirements are documented (none expected for
      public access).
- [ ] Credentials, cookies, tokens, and private links will not be committed.

## Destination

- [ ] Raw downloaded data will go under `data/raw/soilgrids_250m_sediment_candidate/`.
- [ ] Temporary downloads will go under `data/tmp/soilgrids_250m_sediment_candidate/`.
- [ ] Validation records will go under `data/validation/soilgrids_250m_sediment_candidate/` if
      promoted to formal validation use.
- [ ] Processed summaries will go under `outputs/soilgrids_250m_sediment_candidate/`.
- [ ] No real downloaded data will be copied into `context/` or `ifpm-flood-pipeline/`.

## Registry

- [ ] A dataset registry note exists under `context/docs/data-management/registry/`.
- [ ] The note states whether the download is reusable or exploratory.
- [ ] The registry note includes source, product/version, access date, destination, and use.
- [ ] The registry note includes licence/access constraints.
- [ ] The registry note will include checksum or file-size evidence after download.
- [ ] The registry note will identify the checksum scope and expected/actual files.

## Safety Check

- [ ] The target path is ignored by Git.
- [ ] The command will not overwrite unrelated local data.
- [ ] Partial or failed downloads can be identified and cleaned.
- [ ] SoilGrids will NOT be resampled to the V1 30 m terrain grid as pixel-level truth; it stays
      at native 250 m or as a V1/sub-basin zonal summary.
- [ ] Gate G5 authorization entry is written before download.

## Open Blockers Before Authorization

- Mentor has not confirmed a SoilGrids-based K-factor (see
  `p2_sediment_risk_decision_package_2026-06-15.md` decision questions).
- The pedotransfer function for computing K from soil properties has not been chosen.
- The exact SoilGrids properties and depth slices to download have not been finalized.
- WCS endpoint or COG URLs must be re-verified at access time.

## Completion Evidence

Not applicable (download not attempted).
