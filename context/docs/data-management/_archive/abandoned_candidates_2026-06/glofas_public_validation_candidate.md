# Download Preflight: GloFAS Public Validation Candidate

Status: DRAFT. Pre-download blockers not yet checked. No download authorized. Created as P1 R1.1
scaffolding. The `[ ]` items below must be checked, and Step S3 authorization recorded, before any
real download attempt.

## Scope

- [ ] The dataset has a clear project purpose: Tier A outlet-scale discharge context for V1
      return-period exceedance cross-check.
- [ ] The required study area is known: GloFAS cell nearest the V1 outlet.
- [ ] The required temporal window is known: 1979-2024 reanalysis, focus 1985-2024.
- [ ] The expected disk footprint is acceptable: tens to low hundreds of MB for a scoped subset.
- [ ] The download is not a broad bulk mirror: scoped bounding box and time window only.

## Access And Licence

- [ ] Source URL or portal is recorded in the registry note (CDS).
- [ ] Product/version is recorded.
- [ ] Licence, terms, or citation requirements are checked (confirm Copernicus licence at access).
- [ ] Account, registration, approval, or payment requirements are documented (free CDS account).
- [ ] Credentials, cookies, tokens, and private links will not be committed (CDS API key stays in
      local `~/.cdsapirc`).

## Destination

- [ ] Raw downloaded data will go under `data/raw/glofas_public_validation_candidate/`.
- [ ] Temporary downloads will go under `data/tmp/glofas_public_validation_candidate/`.
- [ ] Validation records will go under `data/validation/glofas_public_validation_candidate/` if
      promoted to formal validation use.
- [ ] Processed summaries will go under `outputs/glofas_public_validation_candidate/`.
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
- [ ] Output will be labelled outlet-scale discharge context, not overland flood validation.
- [ ] GloFAS will not be treated as 30 m information; it stays at its native 0.1 degree grid or
      as a V1/outlet zonal summary.
- [ ] Step S3 authorization entry is written before download.

## Open Blockers Before Authorization

- Mentor has not confirmed Tier A context use (see
  `context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/p1_validation_data_decision_package_2026-06-15.md` decision questions).
- V1 outlet should be accepted or provisionally fixed before extraction is meaningful; the V1
  working boundary is currently `accepted_with_waiver_for_controlled_prototype` only.
- CDS account and local API key must be set up by the operator; key must never be committed.
- Exact CDS dataset record id and request payload must be confirmed at access time.

## Completion Evidence

Not applicable (download not attempted).
