# Download Preflight: EM-DAT Public Validation Candidate

Status: DRAFT. Pre-download blockers not yet checked. No download authorized. Created as P1 R1.1
scaffolding. The `[ ]` items below must be checked, and Step S3 authorization recorded, before any
real download attempt.

## Scope

- [ ] The dataset has a clear project purpose: Tier A temporal/event-magnitude context for V1
      flood-event timeline cross-check.
- [ ] The required study area is known: Zimbabwe national and admin-1.
- [ ] The required temporal window is known: 1985-2024 to overlap DFO and CHIRPS.
- [ ] The expected disk footprint is acceptable: tens of MB.
- [ ] The download is not a broad bulk mirror: scoped to EM-DAT Zimbabwe-relevant records.

## Access And Licence

- [ ] Source URL or portal is recorded in the registry note.
- [ ] Product/version is recorded.
- [ ] Licence, terms, or citation requirements are checked (confirm CC BY-NC-SA on HDX resource
      at access time; confirm EM-DAT site terms if site export used).
- [ ] Account, registration, approval, or payment requirements are documented.
- [ ] Credentials, cookies, tokens, and private links will not be committed.

## Destination

- [ ] Raw downloaded data will go under `data/raw/emdat_public_validation_candidate/`.
- [ ] Temporary downloads will go under `data/tmp/emdat_public_validation_candidate/`.
- [ ] Validation records will go under `data/validation/emdat_public_validation_candidate/` if
      the dataset is later promoted to formal validation use.
- [ ] Processed summaries will go under `outputs/emdat_public_validation_candidate/`.
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
- [ ] Output will be labelled temporal/magnitude context, not spatial flood validation.
- [ ] Step S3 authorization entry is written before download.

## Open Blockers Before Authorization

- Mentor has not confirmed Tier A context use (see
  `context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/p1_validation_data_decision_package_2026-06-15.md` decision questions).
- HDX resource id must be re-verified at access time.
- Exact licence field must be confirmed at access time.

## Completion Evidence

Not applicable (download not attempted).
